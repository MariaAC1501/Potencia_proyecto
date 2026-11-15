function [Bprime, Bdouble] = fast_decoupled_matrices(caseData, index)
%FAST_DECOUPLED_MATRICES Forma B' y B'' del método desacoplado rápido.
% Se ignoran R, shunts, carga capacitiva y desplazamiento de fase.
Bprime = zeros(caseData.nBus);
Bdouble = zeros(caseData.nBus);
for k = 1:height(caseData.branch)
    if caseData.branch.STATUS(k) == 0, continue; end
    i = index(caseData.branch.F_BUS(k));
    j = index(caseData.branch.T_BUS(k));
    x = caseData.branch.BR_X(k);
    tap = caseData.branch.TAP(k);
    if abs(tap) < 1e-14, tap = 1; end
    b = 1/x;
    Bprime(i,i) = Bprime(i,i) + b/tap^2;
    Bprime(j,j) = Bprime(j,j) + b;
    Bprime(i,j) = Bprime(i,j) - b/tap;
    Bprime(j,i) = Bprime(j,i) - b/tap;
    Bdouble(i,i) = Bdouble(i,i) + b;
    Bdouble(j,j) = Bdouble(j,j) + b;
    Bdouble(i,j) = Bdouble(i,j) - b;
    Bdouble(j,i) = Bdouble(j,i) - b;
end
end
