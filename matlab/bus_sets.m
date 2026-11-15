function [slack, pv, pq] = bus_sets(caseData)
%BUS_SETS Devuelve índices efectivos; una PV sin generación activa es PQ.
types = caseData.bus.TYPE;
[~, regulated] = voltage_setpoints(caseData);
slack = find(types == 3);
pv = find(types == 2 & regulated);
pq = find(types == 1 | (types == 2 & ~regulated));
end
