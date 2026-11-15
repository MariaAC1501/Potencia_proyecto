function [Pspec, Qspec] = specified_power(caseData, index)
%SPECIFIED_POWER Devuelve generación menos carga en por unidad.
n = caseData.nBus;
Pspec = -caseData.bus.PD / caseData.baseMVA;
Qspec = -caseData.bus.QD / caseData.baseMVA;
for k = 1:height(caseData.gen)
    if caseData.gen.STATUS(k) ~= 0
        i = index(caseData.gen.GEN_BUS(k));
        Pspec(i) = Pspec(i) + caseData.gen.PG(k)/caseData.baseMVA;
        Qspec(i) = Qspec(i) + caseData.gen.QG(k)/caseData.baseMVA;
    end
end
Pspec = reshape(Pspec, n, 1);
Qspec = reshape(Qspec, n, 1);
end
