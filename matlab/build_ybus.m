function [Ybus, index] = build_ybus(caseData)
%BUILD_YBUS Forma la matriz de admitancias nodales.
ids = caseData.bus.BUS_I;
n = numel(ids);
index = containers.Map('KeyType','double', 'ValueType','double');
for k = 1:n
    index(ids(k)) = k;
end
Ybus = complex(zeros(n));
for k = 1:n
    Ybus(k,k) = Ybus(k,k) + (caseData.bus.GS(k) + 1i*caseData.bus.BS(k)) / caseData.baseMVA;
end
for k = 1:height(caseData.branch)
    if caseData.branch.STATUS(k) == 0, continue; end
    i = index(caseData.branch.F_BUS(k));
    j = index(caseData.branch.T_BUS(k));
    z = caseData.branch.BR_R(k) + 1i*caseData.branch.BR_X(k);
    ys = 1/z;
    charging = 1i*caseData.branch.BR_B(k)/2;
    tapMag = caseData.branch.TAP(k);
    if abs(tapMag) < 1e-14, tapMag = 1; end
    tap = tapMag * exp(1i*pi/180*caseData.branch.SHIFT(k));
    Yff = (ys + charging)/(tap*conj(tap));
    Yft = -ys/conj(tap);
    Ytf = -ys/tap;
    Ytt = ys + charging;
    Ybus(i,i) = Ybus(i,i) + Yff;
    Ybus(i,j) = Ybus(i,j) + Yft;
    Ybus(j,i) = Ybus(j,i) + Ytf;
    Ybus(j,j) = Ybus(j,j) + Ytt;
end
end
