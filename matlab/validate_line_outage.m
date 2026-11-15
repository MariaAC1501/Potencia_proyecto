function branchRow = validate_line_outage(baseCase, scenarioCase, fromBus, toBus)
%VALIDATE_LINE_OUTAGE Exige un único cambio de dato y ausencia de islas.
if nargin < 3, fromBus = 26; toBus = 30; end
assert(baseCase.baseMVA == scenarioCase.baseMVA && ...
    isequaln(baseCase.bus, scenarioCase.bus) && isequaln(baseCase.gen, scenarioCase.gen), ...
    'powerflow:ScenarioChanges', 'El escenario no debe cambiar barras, generadores ni base MVA.');
br = baseCase.branch;
branchRow = find((br.F_BUS == fromBus & br.T_BUS == toBus) | ...
    (br.F_BUS == toBus & br.T_BUS == fromBus));
assert(isscalar(branchRow), 'powerflow:OutageNotUnique', ...
    'Debe existir exactamente una rama entre las barras %g y %g.', fromBus, toBus);
assert(br.STATUS(branchRow) == 1, 'powerflow:InactiveOutage', ...
    'La rama a retirar debe estar activa en el caso base.');
expected = br;
expected.STATUS(branchRow) = 0;
assert(isequaln(expected, scenarioCase.branch), 'powerflow:ScenarioChanges', ...
    'El único cambio permitido es STATUS=0 en la rama %g–%g.', fromBus, toBus);
active = scenarioCase.branch.STATUS ~= 0;
[~, from] = ismember(br.F_BUS(active), baseCase.bus.BUS_I);
[~, to] = ismember(br.T_BUS(active), baseCase.bus.BUS_I);
components = conncomp(graph(from, to, [], baseCase.nBus));
assert(numel(unique(components)) == 1, 'powerflow:IslandedScenario', ...
    'El escenario crea islas: no se puede resolver con una única Slack.');
end
