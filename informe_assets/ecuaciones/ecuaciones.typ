#set page(width: 17cm, height: auto, margin: 8pt)
#set text(size: 11pt)
$ S_("pu") = frac(S, S_("base")), quad Z_("base") = frac(U_("base")^2, S_("base")) $
#pagebreak()
$ P_i^("spec") = frac(P_(G i) - P_(D i), S_("base")) $
#pagebreak()
$ Q_i^("spec") = frac(Q_(G i) - Q_(D i), S_("base")) $
#pagebreak()
$ y = frac(1, r + j x), quad t = tau exp(j phi) $
#pagebreak()
$ Y_(f f) = frac(y + j b/2, t overline(t)), quad Y_(f t) = -frac(y, overline(t)) $
#pagebreak()
$ Y_(t f) = -frac(y, t), quad Y_(t t) = y + j b/2 $
#pagebreak()
$ Y_(i i)^("sh") = frac("GS"_i + j "BS"_i, S_("base")) $
#pagebreak()
$ I_i = sum_(k=1)^n Y_(i k) V_k, quad S_i = V_i overline(I_i) $
#pagebreak()
$ V_i = U_i exp(j theta_i), quad Y_(i k) = G_(i k) + j B_(i k) $
#pagebreak()
$ theta_(i k) = theta_i - theta_k $
#pagebreak()
$ P_i^("calc") = U_i sum_(k=1)^n U_k (G_(i k) cos(theta_(i k)) + B_(i k) sin(theta_(i k))) $
#pagebreak()
$ Q_i^("calc") = U_i sum_(k=1)^n U_k (G_(i k) sin(theta_(i k)) - B_(i k) cos(theta_(i k))) $
#pagebreak()
$ Delta P_i = P_i^("spec") - P_i^("calc"), quad Delta Q_i = Q_i^("spec") - Q_i^("calc") $
#pagebreak()
$ Delta S = mat(Delta P_A; Delta Q_("PQ")), quad e = norm(Delta S)_infinity $
#pagebreak()
$ J = mat(H, N; M, L) $
#pagebreak()
$ J mat(Delta theta_A; Delta U_("PQ")) = mat(Delta P_A; Delta Q_("PQ")) $
#pagebreak()
$ H_(i k) = U_i U_k (G_(i k) sin(theta_(i k)) - B_(i k) cos(theta_(i k))) $
#pagebreak()
$ N_(i k) = U_i (G_(i k) cos(theta_(i k)) + B_(i k) sin(theta_(i k))) $
#pagebreak()
$ M_(i k) = -U_i U_k (G_(i k) cos(theta_(i k)) + B_(i k) sin(theta_(i k))) $
#pagebreak()
$ L_(i k) = U_i (G_(i k) sin(theta_(i k)) - B_(i k) cos(theta_(i k))) $
#pagebreak()
$ H_(i i) = -Q_i^("calc") - B_(i i) U_i^2 $
#pagebreak()
$ N_(i i) = frac(P_i^("calc"), U_i) + G_(i i) U_i $
#pagebreak()
$ M_(i i) = P_i^("calc") - G_(i i) U_i^2 $
#pagebreak()
$ L_(i i) = frac(Q_i^("calc"), U_i) - B_(i i) U_i $
#pagebreak()
$ V_i^("cand") = frac(frac(P_i^("spec") - j Q_i^("use"), overline(V_i)) - sum_(k != i) Y_(i k) V_k, Y_(i i)) $
#pagebreak()
$ V_i^("rel") = V_i + alpha (V_i^("cand") - V_i) $
#pagebreak()
$ V_i^("new") = U_i^("set") exp(j arg(V_i^("rel"))) $
#pagebreak()
$ B'_("rama") = frac(1, x) mat(frac(1, tau^2), -frac(1, tau); -frac(1, tau), 1) $
#pagebreak()
$ B''_("rama") = frac(1, x) mat(1, -1; -1, 1) $
#pagebreak()
$ B' Delta theta_A = frac(Delta P_A, U_A) $
#pagebreak()
$ B'' Delta U_("PQ") = frac(Delta Q_("PQ"), U_("PQ")) $
#pagebreak()
$ S_f = S_("base") V_f overline(I_f), quad S_t = S_("base") V_t overline(I_t) $
#pagebreak()
$ P_("rama") = "Re"(S_f + S_t), quad Q_("rama") = "Im"(S_f + S_t) $
#pagebreak()
$ sum_i P_(G i) - sum_i P_(D i) = sum_l P_("rama", l) + sum_i "GS"_i U_i^2 $
#pagebreak()
$ sum_i Q_(G i) - sum_i Q_(D i) = sum_l Q_("rama", l) - sum_i "BS"_i U_i^2 $