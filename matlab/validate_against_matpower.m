function [summary, metadata] = validate_against_matpower(matpowerPath, outputFile)
%VALIDATE_AGAINST_MATPOWER Contrasta los tres métodos con MATPOWER.
%   [summary, metadata] = validate_against_matpower('C:/ruta/matpower8.1');
%   Usa IEEE-14, IEEE-118 e IEEE-300. No interviene en main ni en la GUI.
%   IEEE-118 se contrasta además con el case118.m oficial de MATPOWER.
%   Exporta resumen, errores barra/rama y metadatos. Falla si un umbral
%   de aceptación no se cumple. No guarda cambios en el path de MATLAB.

matlabDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(matlabDir);
if nargin < 1, matpowerPath = ''; end
if nargin < 2 || isempty(outputFile)
    outputFile = fullfile(projectRoot, 'validacion_MATPOWER.xlsx');
end
oldPath = path;
restorePath = onCleanup(@() path(oldPath)); %#ok<NASGU>
addpath(matlabDir);
if strlength(string(matpowerPath)) > 0
    if ~isfile(fullfile(matpowerPath, 'install_matpower.m'))
        error('Indique la raíz de MATPOWER, que contiene install_matpower.m.');
    end
    addpath(matpowerPath);
    assert(install_matpower(1, 0, 0), 'No se pudo activar MATPOWER.');
end
if isempty(which('runpf')) || isempty(which('mpver'))
    error('MATPOWER no está disponible. Indique su carpeta como primer argumento.');
end
matpowerRoot = fileparts(fileparts(which('runpf')));
versionInfo = mpver('all');
thresholds = struct('VM_pu', 1e-7, 'VA_deg', 1e-5, ...
    'BranchP_MW', 1e-4, 'BranchQ_MVAr', 1e-4, 'PLoss_MW', 1e-4, ...
    'QLoss_MVAr', 1e-4, 'SlackP_MW', 1e-4, 'SlackQ_MVAr', 1e-4);
options = struct('tolerance', 1e-8, 'maxIterations', 1000, ...
    'relaxation', 1.5, 'enforceQLimits', false);
mpopt = mpoption('verbose', 0, 'out.all', 0, 'pf.alg', 'NR', ...
    'pf.tol', 1e-10, 'pf.nr.max_it', 30, 'pf.enforce_q_lims', 0);
caseNames = {'IEEE14', 'IEEE118', 'IEEE300'};
methods = {'Newton-Raphson', 'Gauss-Seidel', 'fdlf'};
prefixes = {'NR', 'GS', 'FDLF'};
rows = cell(9, 18);
details = cell(9, 2);
sourceCheck = struct();
n = 0;
for c = 1:numel(caseNames)
    caseName = caseNames{c};
    caseData = load_case_excel(fullfile(projectRoot, 'data', [caseName, '.xlsx']));
    mpc = as_matpower_case(caseData);
    referenceDescription = 'MATPOWER NR sobre los mismos datos Excel';
    if strcmp(caseName, 'IEEE118')
        official = loadcase(fullfile(matpowerRoot, 'data', 'case118.m'));
        sourceCheck = compare_official_case(mpc, official);
        assert(sourceCheck.matches, ...
            'IEEE118.xlsx no coincide con el case118 oficial: revise las entradas.');
        mpc = official;
        referenceDescription = 'case118.m oficial MATPOWER; entradas verificadas';
    end
    reference = runpf(mpc, mpopt);
    assert(reference.success, 'MATPOWER no convergió para %s.', caseName);
    [present, order] = ismember(caseData.bus.BUS_I, reference.bus(:, 1));
    assert(all(present), 'Barras faltantes en la referencia de %s.', caseName);
    assert(isequal(caseData.branch.F_BUS, reference.branch(:, 1)) && ...
        isequal(caseData.branch.T_BUS, reference.branch(:, 2)), ...
        'El orden de ramas de la referencia no coincide.');
    refVM = reference.bus(order, 8);
    refVA = reference.bus(order, 9);
    refPLoss = sum(reference.branch(:, 14) + reference.branch(:, 16));
    refQLoss = sum(reference.branch(:, 15) + reference.branch(:, 17));
    slackID = caseData.bus.BUS_I(caseData.bus.TYPE == 3);
    slackUnits = reference.gen(:,1) == slackID & reference.gen(:,8) > 0;
    refSlackP = sum(reference.gen(slackUnits,2));
    refSlackQ = sum(reference.gen(slackUnits,3));
    for k = 1:numel(methods)
        own = solve_power_flow(caseData, methods{k}, options);
        dVM = abs(own.busResults.VM_pu - refVM);
        dVA = abs(mod(own.busResults.VA_deg - refVA + 180, 360) - 180);
        br = own.branchResults;
        dPF = abs(br.P_from_MW - reference.branch(:, 14));
        dQF = abs(br.Q_from_MVAr - reference.branch(:, 15));
        dPT = abs(br.P_to_MW - reference.branch(:, 16));
        dQT = abs(br.Q_to_MVAr - reference.branch(:, 17));
        maxP = max([dPF; dPT]);
        maxQ = max([dQF; dQT]);
        dLoss = abs(own.summary.P_loss_MW - refPLoss);
        dQLoss = abs(own.summary.Q_loss_MVAr - refQLoss);
        ownSlack = own.busResults(own.busResults.BUS_I == slackID,:);
        dSlackP = abs(ownSlack.P_gen_calculada_MW-refSlackP);
        dSlackQ = abs(ownSlack.Q_gen_calculada_MVAr-refSlackQ);
        passed = own.converged && own.maxMismatch <= options.tolerance && ...
            max(dVM) <= thresholds.VM_pu && max(dVA) <= thresholds.VA_deg && ...
            maxP <= thresholds.BranchP_MW && maxQ <= thresholds.BranchQ_MVAr && ...
            dLoss <= thresholds.PLoss_MW && dQLoss <= thresholds.QLoss_MVAr && ...
            dSlackP <= thresholds.SlackP_MW && dSlackQ <= thresholds.SlackQ_MVAr;
        n = n + 1;
        rows(n, :) = {caseName, own.method, max(dVM), max(dVA), maxP, maxQ, ...
            dLoss, passed, own.iterations, own.maxMismatch, referenceDescription, ...
            dQLoss, dSlackP, dSlackQ, refPLoss, refQLoss, refSlackP, refSlackQ};
        details{n, 1} = table(caseData.bus.BUS_I, own.busResults.VM_pu, refVM, ...
            dVM, own.busResults.VA_deg, refVA, dVA, 'VariableNames', ...
            {'BUS_I','Own_VM_pu','Reference_VM_pu','AbsVMError_pu', ...
            'Own_VA_deg','Reference_VA_deg','AbsVAError_deg'});
        details{n, 2} = table(br.Rama, br.Desde, br.Hasta, ...
            br.P_from_MW, reference.branch(:, 14), dPF, ...
            br.Q_from_MVAr, reference.branch(:, 15), dQF, ...
            br.P_to_MW, reference.branch(:, 16), dPT, ...
            br.Q_to_MVAr, reference.branch(:, 17), dQT, 'VariableNames', ...
            {'Rama','Desde','Hasta','Own_Pfrom_MW','Ref_Pfrom_MW','AbsPfromError_MW', ...
            'Own_Qfrom_MVAr','Ref_Qfrom_MVAr','AbsQfromError_MVAr', ...
            'Own_Pto_MW','Ref_Pto_MW','AbsPtoError_MW', ...
            'Own_Qto_MVAr','Ref_Qto_MVAr','AbsQtoError_MVAr'});
        fprintf('%s / %s: VM=%.3e pu, VA=%.3e grados, P_rama=%.3e MW, Q_rama=%.3e MVAr, pasa=%d\n', ...
            caseName, prefixes{k}, max(dVM), max(dVA), maxP, maxQ, passed);
    end
end
summary = cell2table(rows, 'VariableNames', {'Case','Method','MaxAbsVMError_pu', ...
    'MaxAbsVAError_deg','MaxAbsBranchPError_MW','MaxAbsBranchQError_MVAr', ...
    'AbsPLossError_MW','Passed','Iterations','MaxMismatch_pu','Reference', ...
    'AbsQLossError_MVAr','AbsSlackPError_MW','AbsSlackQError_MVAr', ...
    'ReferencePLoss_MW','ReferenceQLoss_MVAr','ReferenceSlackP_MW','ReferenceSlackQ_MVAr'});
metadata = struct('matlabVersion', version, 'matpowerVersion', versionInfo.Version, ...
    'matpowerReleaseDate', versionInfo.Date, 'timestampUTC', ...
    char(datetime('now', 'TimeZone', 'UTC', 'Format', "yyyy-MM-dd'T'HH:mm:ss'Z'")), ...
    'referenceAlgorithm', 'MATPOWER Newton-Raphson', 'referenceTolerance_pu', 1e-10, ...
    'ownTolerance_pu', options.tolerance, 'enforceQLimits', false, ...
    'thresholds', thresholds, 'officialIEEE118InputCheck', sourceCheck, ...
    'allPassed', all(summary.Passed), 'comparisons', table2struct(summary));

% Se escribe primero en un libro temporal para no dejar una mezcla de corridas.
[outputDir, outputName] = fileparts(outputFile);
if isempty(outputDir), outputDir = pwd; end
if ~isfolder(outputDir), mkdir(outputDir); end
tempOutput = [tempname(outputDir), '.xlsx'];
cleanupTemp = onCleanup(@() delete_if_exists(tempOutput)); %#ok<NASGU>
writetable(summary, tempOutput, 'Sheet', 'resumen');
metaTable = table(string({'MATLAB';'MATPOWER';'UTC';'ReferenceTolerance_pu'; ...
    'OwnTolerance_pu';'MaxVM_pu';'MaxVA_deg';'MaxBranchP_MW'; ...
    'MaxBranchQ_MVAr';'MaxPLoss_MW';'OfficialIEEE118Matches'}), ...
    string({metadata.matlabVersion;metadata.matpowerVersion;metadata.timestampUTC; ...
    1e-10;options.tolerance;thresholds.VM_pu;thresholds.VA_deg; ...
    thresholds.BranchP_MW;thresholds.BranchQ_MVAr;thresholds.PLoss_MW;sourceCheck.matches}), ...
    'VariableNames', {'Key','Value'});
writetable(metaTable, tempOutput, 'Sheet', 'metadatos');
for c = 1:numel(caseNames)
    for k = 1:numel(methods)
        n = (c - 1)*numel(methods) + k;
        prefix = [caseNames{c}, '_', prefixes{k}];
        writetable(details{n, 1}, tempOutput, 'Sheet', [prefix, '_bus']);
        writetable(details{n, 2}, tempOutput, 'Sheet', [prefix, '_branch']);
    end
end
[ok, message] = movefile(tempOutput, outputFile, 'f');
assert(ok, 'No se pudo guardar la validación: %s', message);
jsonFile = fullfile(outputDir, [outputName, '.json']);
fid = fopen(jsonFile, 'w', 'n', 'UTF-8');
assert(fid ~= -1, 'No se pudo crear %s.', jsonFile);
closeFile = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s\n', jsonencode(metadata, 'PrettyPrint', true));
assert(all(summary.Passed), 'Hay comparaciones fuera de tolerancia. Consulte %s.', outputFile);
fprintf('Validación externa: %d/%d comparaciones aprobadas. Libro: %s\n', ...
    sum(summary.Passed), height(summary), outputFile);
end

function mpc = as_matpower_case(c)
mpc = struct('version', '2', 'baseMVA', c.baseMVA);
mpc.bus = c.bus{:, {'BUS_I','TYPE','PD','QD','GS','BS','AREA','VM','VA', ...
    'BASE_KV','ZONE','VMAX','VMIN'}};
mpc.gen = zeros(c.nGen, 21);
mpc.gen(:, 1:10) = c.gen{:, {'GEN_BUS','PG','QG','QMAX','QMIN', ...
    'VG','MBASE','STATUS','PMAX','PMIN'}};
mpc.branch = c.branch{:, {'F_BUS','T_BUS','BR_R','BR_X','BR_B','RATE_A', ...
    'RATE_B','RATE_C','TAP','SHIFT','STATUS','ANGMIN','ANGMAX'}};
end

function check = compare_official_case(own, official)
% Los taps 0 y 1 representan la misma relación unitaria.
[a, ia] = sort(own.bus(:, 1)); [b, ib] = sort(official.bus(:, 1));
check = struct('matches', false, 'baseMVAError', abs(own.baseMVA-official.baseMVA), ...
    'maxBusDataError', inf, 'maxGenDataError', inf, 'maxBranchDataError', inf);
if ~isequal(a, b) || ~isequal(size(own.gen(:,1:10)), size(official.gen(:,1:10))) || ...
        ~isequal(size(own.branch), size(official.branch(:,1:13)))
    return;
end
ownBranch = own.branch; refBranch = official.branch(:,1:13);
ownBranch(ownBranch(:,9)==0,9) = 1;
refBranch(refBranch(:,9)==0,9) = 1;
check.maxBusDataError = max(abs(own.bus(ia,:) - official.bus(ib,1:13)), [], 'all');
check.maxGenDataError = max(abs(own.gen(:,1:10) - official.gen(:,1:10)), [], 'all');
check.maxBranchDataError = max(abs(ownBranch - refBranch), [], 'all');
check.matches = check.baseMVAError < 1e-12 && check.maxBusDataError < 1e-12 && ...
    check.maxGenDataError < 1e-12 && check.maxBranchDataError < 1e-12;
end

function delete_if_exists(filename)
if isfile(filename), delete(filename); end
end
