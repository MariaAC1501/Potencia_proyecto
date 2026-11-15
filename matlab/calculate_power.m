function [Pcalc, Qcalc] = calculate_power(Ybus, V, baseMVA)
%CALCULATE_POWER Calcula inyecciones nodales en MW/MVAr.
S = V .* conj(Ybus*V) * baseMVA;
Pcalc = real(S);
Qcalc = imag(S);
end
