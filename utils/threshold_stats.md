# Relationship of jaccard threshold and percentage of changed words

The percentage of changed documents identified as changed based on 
* Percentage of document tokens changed
* Jaccard coefficient threshold <code>jaccard(d_orig, d_mod) > threshold ==> documents are same</code> 


| perc changed | 0.001 | 0.01  | 0.025 | 0.05  | 0.1   | 0.2   | 0.5 |
|-----------|-------|-------|-------|-------|-------|-------|-----|
| threshold |       |       |       |       |       |       |     |
| 0.8       | 0.469 | 0.001 | 0.001 | 0.003 | 0.18  | 0.872 | 1.0 |
| 0.9       | 0.469 | 0.001 | 0.051 | 0.521 | 0.929 | 1.0   | 1.0 |
| 0.95      | 0.469 | 0.029 | 0.625 | 0.953 | 0.998 | 1.0   | 1.0 |
| 0.99      | 0.496 | 0.837 | 0.989 | 1.0   | 1.0   | 1.0   | 1.0 |