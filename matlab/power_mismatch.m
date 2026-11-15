function [mismatch, err, Pcalc, Qcalc] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq)
%POWER_MISMATCH Calcula mismatch P/Q en por unidad.
S = V .* conj(Ybus*V);
Pcalc = real(S);
Qcalc = imag(S);
allBuses = (1:numel(V))';
angleBuses = allBuses(~ismember(allBuses, slack));
dP = Pspec(angleBuses) - Pcalc(angleBuses);
dQ = Qspec(pq) - Qcalc(pq);
mismatch = [dP; dQ];
if isempty(mismatch), err = 0; else, err = max(abs(mismatch)); end
end
