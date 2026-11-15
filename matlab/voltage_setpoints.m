function [vm, regulated] = voltage_setpoints(caseData)
%VOLTAGE_SETPOINTS Consignas VG de unidades activas en PV/Slack.
% PQ (también PV sin unidades activas) usa VM solo como valor inicial.
% Sin columna VG se conserva VM por compatibilidad. Varias unidades en una
% barra deben coincidir dentro de 1e-10 relativo (con escala mínima 1 pu).
vm = caseData.bus.VM;
types = caseData.bus.TYPE;
active = caseData.gen.STATUS ~= 0;
regulated = (types == 2 | types == 3) & ...
    ismember(caseData.bus.BUS_I, caseData.gen.GEN_BUS(active));
if any(types == 3 & ~regulated)
    error('powerflow:InactiveSlack', 'La barra Slack debe tener al menos un generador activo (STATUS distinto de cero).');
end
hasVG = ismember('VG', caseData.gen.Properties.VariableNames);
for i = find(regulated)'
    rows = active & caseData.gen.GEN_BUS == caseData.bus.BUS_I(i);
    if hasVG
        values = caseData.gen.VG(rows);
    else
        values = vm(i);
    end
    if ~isreal(values) || any(~isfinite(values) | values <= 0)
        error('powerflow:InvalidVG', ...
            'Las consignas VG activas en la barra %g deben ser positivas y finitas.', caseData.bus.BUS_I(i));
    end
    if max(values)-min(values) > 1e-10*max(1, max(abs(values)))
        error('powerflow:ConflictingVG', ...
            'Consignas VG contradictorias entre generadores activos en la barra %g.', caseData.bus.BUS_I(i));
    end
    vm(i) = values(1);
end
if ~isreal(vm) || any(~isfinite(vm) | vm <= 0)
    error('powerflow:InvalidVoltage', 'Los voltajes iniciales o regulados deben ser positivos y finitos.');
end
end
