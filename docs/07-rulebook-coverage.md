# Rulebook coverage audit

This file separates tested calculation helpers from end-to-end question support. It is an implementation audit, not a claim that the competition rulebook is complete. No public-test answers or scores were used to build this matrix.

| Rulebook area | Current code and focused tests | Status before submission cutover |
| --- | --- | --- |
| Valid sales orders, returned/cancelled orders, shipping still eligible | `application/sales.py`; `SalesTests` | Unit-tested normalized rows; source discovery and routing are not connected |
| Revenue from discounted line totals; order discount and shipping excluded | `application/sales.py`; `SalesTests` | Unit-tested; VAT/discount source mapping is not connected |
| Revenue by customer group and whole-shop denominator | `application/sales.py`; `SalesTests` | Unit-tested generic dimension; payment-method extraction is not connected |
| Period parsing, inclusive dates, month/week, comparisons, Tet, shift and weekday counts | `application/periods.py`; `PeriodTests` | Utility tests exist; handlers do not consistently consume every resolved period |
| Product rank by base quantity, distinct orders, service-fee exclusion | `application/product_reports.py`; `ProductReportTests` | Unit-tested normalized input; unit conversion/catalog joins are not connected |
| Customer identity and customer ranks | `application/customers.py`; `CustomerIdentityTests` | Unit-tested; order-source mapping and final table output are not connected |
| Staff and busy-window ranks | `application/staff_reports.py`; `ProductReportTests` | Unit-tested; staff and creation-time source mapping is not connected |
| Receivables, debt activity, COD/sales-platform exclusion | `application/debt.py`; `DebtTests` | Partial: callers must supply an `excluded` flag; debt-source policy and customer grouping are not connected |
| Purchase totals, cancellation, source sheets and split files | `application/purchases.py`; `PurchaseTests`; benchmark sample | End-to-end for the benchmarked purchase-total shape; broader purchase intents are not connected |
| Supplier rank, weighted purchase price and net quantities | `application/purchase_reports.py`; `SupplierReportTests` | Unit-tested normalized inputs; source bindings and unit conversion are not connected |
| End-of-day stock and unsold products | `application/inventory.py`; `InventoryTests` | Unit-tested normalized movements; stock-ledger reconstruction is not connected |
| Selling-price and price-change calculations | `application/pricing.py`; `PricingTests` | Partial: price-history windows and runtime source mappings are not connected |
| Gross and net profit | `application/profit.py`; `ProfitTests` | Unit-tested; cost and expense ledgers are not connected |
| Cafe size/topping classification | `application/cafe.py`; `CafeTests` | Partial: current parser accepts more than the rulebook's trailing `(M)`/`(L)` convention |
| Pharmacy classification and lots | `application/pharmacy.py`; `PharmacyTests` | Unit-tested; catalog/lot loading and prescription revenue denominator are not connected |
| Construction delivery batches | `application/construction.py`; `ConstructionTests` | Unit-tested; source rows must already represent one delivery per order/batch |
| Baby-shop totals, sizes and members | `application/baby_shop.py`; `BabyShopTests` | Unit-tested generic fields; source joins and answer formatting are not connected |
| Repair visits, services, warranties and repeat plates | `application/repair.py`; `RepairTests` | Unit-tested generic rows; service text splitting, source aliases and warranty joins are not connected |
| Phone trade-ins, installments, model and warranty | `application/phones.py`; `PhoneTests` | Unit-tested generic rows; source workbook joins and quarter/model grouping are not connected |
| Evidence, abstain/unanswerable distinction and submission shape | `application/evidence.py`, `application/formatting.py`; evidence and formatting tests | Utility-tested; table serialization is not used by the current runner |
| Duplicate rows, grouped blanks, source normalization and read-only inputs | `data/normalize.py`, `data/sources.py`; `SourceTests` | Unit-tested helpers; the sales pipeline does not yet apply grouped-row normalization to every source |

## Cutover blockers

- The current `DeterministicAgent` routes only the purchase-total shape. Other handlers are not reachable from the question runner.
- Table-producing handlers still return internal row dictionaries. The typed table serializer exists but is not wired through all handlers and the runner.
- Rulebook edge cases that require real source joins need source-specific fixtures before they can be marked covered.
- Do not switch the submission entrypoint or remove the legacy pipeline until these gaps are closed and grouped development evaluation is recorded.
