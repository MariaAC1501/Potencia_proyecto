function branchResults = calculate_branch_flows(caseData, V)
%CALCULATE_BRANCH_FLOWS Calcula flujos desde/hacia cada rama.
[~, index] = build_ybus(caseData);
nBranch = height(caseData.branch);
Rama = (1:nBranch)'; Desde = caseData.branch.F_BUS; Hasta = caseData.branch.T_BUS;
Pfrom = zeros(nBranch,1); Qfrom = zeros(nBranch,1); Pto = zeros(nBranch,1); Qto = zeros(nBranch,1);
Sfrom = zeros(nBranch,1); Sto = zeros(nBranch,1); Ploss = zeros(nBranch,1); Qloss = zeros(nBranch,1);
Loading = nan(nBranch,1);
for k = 1:nBranch
    if caseData.branch.STATUS(k) == 0, continue; end
    i = index(Desde(k)); j = index(Hasta(k));
    y = 1/(caseData.branch.BR_R(k)+1i*caseData.branch.BR_X(k));
    b = 1i*caseData.branch.BR_B(k)/2;
    tapMag = caseData.branch.TAP(k); if abs(tapMag) < 1e-14, tapMag = 1; end
    tap = tapMag*exp(1i*pi/180*caseData.branch.SHIFT(k));
    Yff = (y+b)/(tap*conj(tap)); Yft = -y/conj(tap);
    Ytf = -y/tap; Ytt = y+b;
    Ifrom = Yff*V(i)+Yft*V(j); Ito = Ytf*V(i)+Ytt*V(j);
    SfromComplex = V(i)*conj(Ifrom)*caseData.baseMVA;
    StoComplex = V(j)*conj(Ito)*caseData.baseMVA;
    Pfrom(k) = real(SfromComplex); Qfrom(k) = imag(SfromComplex); Sfrom(k) = abs(SfromComplex);
    Pto(k) = real(StoComplex); Qto(k) = imag(StoComplex); Sto(k) = abs(StoComplex);
    Ploss(k) = real(SfromComplex+StoComplex); Qloss(k) = imag(SfromComplex+StoComplex);
    if caseData.branch.RATE_A(k) > 0, Loading(k) = 100*Sfrom(k)/caseData.branch.RATE_A(k); end
end
branchResults = table(Rama, Desde, Hasta, Pfrom, Qfrom, Sfrom, Pto, Qto, Sto, Ploss, Qloss, Loading, ...
    'VariableNames', {'Rama','Desde','Hasta','P_from_MW','Q_from_MVAr','S_from_MVA','P_to_MW','Q_to_MVAr','S_to_MVA','P_loss_MW','Q_loss_MVAr','Loading_percent'});
end
