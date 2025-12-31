

# Place Position TP/SL Order ​

Rate Limit: 10 req/sec/UID

### Description ​

Place Position TP/SL OrderWhen triggered, it will close the position at market price based on the position quantity at that time.Each position can only have one Position TP/SL Order

### HTTP Request ​

* POST /api/v1/futures/tpsl/position/place_order


### Request Parameters ​



| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Trading pair |
| positionId | string | true | Position ID associated with take-profit and stop-loss |
| tpPrice | string | false | Take-profit trigger priceAt least one oftpPriceorslPriceis required. |
| tpStopType | string | false | Take-profit trigger typeLAST_PRICEMARK_PRICEDefault is market price. |
| slPrice | string | false | Stop-loss trigger priceAt least one oftpPriceorslPriceis required. |
| slStopType | string | false | Stop-loss trigger typeLAST_PRICEMARK_PRICEDefault is market price. |

Request Examplebash
```
curl -X 'POST'  --location 'https://fapi.bitunix.com/api/v1/futures/tpsl/position/place_order' \
   -H "api-key:*******" \
   -H "sign:*" \
   -H "nonce:your-nonce" \
   -H "timestamp:1659076670000" \
   -H "language:en-US" \
   -H "Content-Type: application/json" \
 --data '{"symbol":"BTCUSDT","positionId":"111","tpPrice":"12","tpStopType":"LAST_PRICE","slPrice":"9","slStopType":"LAST_PRICE"}'
```


### Response Parameters ​



| Parameter | Type | Description |
| --- | --- | --- |
| orderId | string | TP/SL Order ID |

Response Examplejson
```
{"code":0,"data":{"orderId":"11111"},"msg":"Success"}
```
