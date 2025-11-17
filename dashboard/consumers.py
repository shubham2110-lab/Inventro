import json
from channels.generic.websocket import AsyncWebsocketConsumer


class LowStockConsumer(AsyncWebsocketConsumer):
    group_name = "low_stock"

    async def connect(self):
        user = self.scope.get("user")
        # Restrict to authenticated users so anonymous visitors don't receive internal alerts
        if not user or not user.is_authenticated:
            await self.close()
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def low_stock_alert(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "low_stock",
                    "item": event.get("item", {}),
                }
            )
        )
