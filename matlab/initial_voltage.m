function V = initial_voltage(caseData)
%INITIAL_VOLTAGE Usa VG en barras reguladas y VM inicial en barras PQ.
vm = voltage_setpoints(caseData);
V = vm .* exp(1i*pi/180*caseData.bus.VA);
end
