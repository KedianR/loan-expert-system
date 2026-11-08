% toy_rules.pl
% Throwaway toy Prolog rule file for Spike S1 (WP-02).
% NEVER used by the product. Lives only under spikes/s1/.
%
% Two toy knockout rules:
%   k_score: credit score below minimum
%   k_income: monthly income below minimum
%
% fired_rule(Score, Income, MinScore, MinIncome, Rule)

fired_rule(Score, _Income, MinScore, _MinIncome, k_score) :-
    Score < MinScore.

fired_rule(_Score, Income, _MinScore, MinIncome, k_income) :-
    Income < MinIncome.

