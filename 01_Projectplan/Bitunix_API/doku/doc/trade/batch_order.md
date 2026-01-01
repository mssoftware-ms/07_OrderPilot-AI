

# Batch Order ​

Rate Limit: 1 req/sec/uid

### Description ​

Place order

### HTTP Request ​

* POST /api/v1/futures/trade/batch_order


### Request Parameters ​



| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Trading pair |
| orderList | list | true | Order list, maximum length: 5 |
| >qty | string | true | Amount (base coin) |
| >price | string | false | Price of the order.Required if the order type isLIMIT |
| >side | string | true | Order directionbuy:BUYsell:SELL |
| >tradeSide | string | true | DirectionOnly required in hedge-modeOpen and Close Notes:For open long, side fill in"BUY"; tradeSide should be "OPEN"For open short, side fill in "SELL"; tradeSide should be "OPEN"For close long, side fill in "BUY"; tradeSide should be "CLOSE"For close short, side fill in "SELL";tradeSide should be "CLOSE" |
| >positionId | string | false | Position IDOnly required when "tradeSide" is "CLOSE" |
| >orderType | string | true | Order typeLIMIT: limit ordersMARKET: market orders |
| >effect | string | false | Order expiration date.Required if the orderType is limitIOC: Immediate or cancelFOK: Fill or killGTC: Good till canceled(default value)POST_ONLY: POST only |
| >clientId | string | false | Customize order ID |
| >reduceOnly | boolean | false | Whether or not to just reduce the position |
| >tpPrice | string | false | take profit trigger price |
| >tpStopType | string | false | take profit trigger typeMARK_PRICELAST_PRICE |
| >tpOrderType | string | false | take profit trigger place order typeLIMITMARKET |
| >tpOrderPrice | string | false | take profit trigger place order priceLIMITMARKETrequired if tpOrderType isLIMIT |
| >slPrice | string | false | stop loss trigger price |
| >slStopType | string | false | stop loss trigger typeMARK_PRICELAST_PRICE |
| >slOrderType | string | false | stop loss trigger place order typeLIMITMARKET |
| >slOrderPrice | string | false | stop loss trigger place order priceLIMITMARKETrequired if slOrderType isLIMIT |

Request Examplebash
```
curl -X 'POST'  --location 'https://fapi.bitunix.com/api/v1/futures/trade/batch_order' \
   -H "api-key:*******" \
   -H "sign:*" \
   -H "nonce:your-nonce" \
   -H "timestamp:1659076670000" \
   -H "language:en-US" \
   -H "Content-Type: application/json" \
 --data '{"symbol":"BTCUSDT","orderList":[{"side":"BUY","price":"60000","qty":"0.5","orderType":"LIMIT","reduceOnly":false,"effect":"GTC","clientId":"c12345","tpPrice":"61000","tpStopType":"MARK","tpOrderType":"LIMIT","tpOrderPrice":"61000.1","slPrice":"59000","slStopType":"LAST","slOrderType":"MARKET"},{"side":"SELL","price":"61000","qty":"0.5","orderType":"LIMIT","reduceOnly":false,"effect":"IOC","clientId":"c12346"}]}'
```


### Response Parameters ​



| Parameter | Type | Description |
| --- | --- | --- |
| successList | list | Successful order list |
| >id | string | order id |
| >clientId | string | client id |
| failureList | list | Failed order list |
| >clientId | string | client id |
| >errorMsg | string | error msg |
| >errorCode | string | error code |

Response Examplejson
```
{"code":0,"data":{"successList":[{"id":"11111","clientId":"22222"}],"failureList":[{"clientId":"22222","errorMsg":"Insufficient balance","errorCode":10012}]},"msg":"Success"}
```
