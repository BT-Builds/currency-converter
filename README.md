# Currency Converter API

Convert currency amounts with realistic e-commerce markup for accurate customer pricing.

## Problem it solves

When building international e-commerce sites, the mid-market exchange rate doesn't match what customers actually pay. Payment processors add 2-4% markup, causing confusion when prices shown to customers differ from expectations. This API calculates realistic converted prices accounting for PayPal/Stripe fees.

## Who needs it

- E-commerce developers building international stores
- Shopify/WooCommerce plugin developers
- SaaS companies pricing in multiple currencies

## Endpoints

### GET /health
Check service status. No auth required.

### POST /convert
Convert currency with fee markup.

**Headers:** Authorization: Bearer YOUR_API_KEY

**Body:**
```json
{
  "from_currency": "USD",
  "to_currency": "EUR",
  "amount": 100.00,
  "fee_type": "stripe"
}
```

**fee_type options:**
- `mid` - No markup (real exchange rate)
- `paypal` - 4% markup
- `stripe` - 2.9% markup
- `wise` - 0.5% markup

### GET /currencies
List supported currency codes.

**Headers:** Authorization: Bearer YOUR_API_KEY

### GET /fee-types
List available fee types and their markups.

## Example

```bash
curl -X POST https://currency-converter.vercel.app/convert \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from_currency":"USD","to_currency":"EUR","amount":100,"fee_type":"stripe"}'
```

## Monetization

List on RapidAPI at $19/month for teams. Target pricing includes 1000 requests/day.