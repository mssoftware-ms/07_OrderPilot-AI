

# Modify Order ​

Rate Limit: 10 req/sec/uid

### Description ​

Interface for order modification, used to modify an pending order, such as its TP/SL and/or price/qty.Attention!!Successful interface response is not necessarily equal to the success of the operation, please use the websocket push message as an accurate judgment of the success of the operation.

### HTTP Request ​

* POST /api/v1/futures/trade/modify_order


### Request Parameters ​



| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| orderId | string | false | Order IDEither orderId or clientId is required. If both are entered, orderId prevails. |
| clientId | string | false | Customize order IDEither orderId or clientId is required. If both are entered, orderId prevails. |
| qty | string | true | Amount (base coin) |
| price | string | true | Price of the order.Required if the order type isLIMIT |
| tpPrice | string | false | take profit trigger price |
| tpStopType | string | false | take profit trigger typeMARK_PRICELAST_PRICE |
| tpOrderType | string | false | take profit trigger place order typeLIMITMARKET |
| tpOrderPrice | string | false | take profit trigger place order priceLIMITMARKETrequired if tpOrderType isLIMIT |
| slPrice | string | false | stop loss trigger price |
| slStopType | string | false | stop loss trigger typeMARK_PRICELAST_PRICE |
| slOrderType | string | false | stop loss trigger place order typeLIMITMARKET |
| slOrderPrice | string | false | stop loss trigger place order priceLIMITMARKETrequired if slOrderType isLIMIT |

Request Examplebash
```
curl -X 'POST'  --location 'https://fapi.bitunix.com/api/v1/futures/trade/modify_order' \
   -H "api-key:*******" \
   -H "sign:*" \
   -H "nonce:your-nonce" \
   -H "timestamp:1659076670000" \
   -H "language:en-US" \
   -H "Content-Type: application/json" \
 --data '{"orderId":"1111","symbol":"BTCUSDT","price":"60000","qty":"0.5","tpPrice":"61000","tpStopType":"MARK","tpOrderType":"LIMIT","tpOrderPrice":"61000.1"}'
```


### Response Parameters ​



| Parameter | Type | Description |
| --- | --- | --- |
| orderId | string | order id |
| clientId | string | client id |

Response Examplejson
```
{"code":0,"data":{"orderId":"11111","clientId":"22222"},"msg":"Success"}
```
