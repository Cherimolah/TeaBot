import aiosqlite3
import asyncio


class MainDB:

    async def connection(self):
        self.db: aiosqlite3.Connection = await aiosqlite3.connect("database.db")
        self.sql: aiosqlite3.Cursor = await self.db.cursor()
        await self.sql.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER, hello_msg TEXT, bye_msg TEXT)",)
        await self.db.commit()


main_db = asyncio.get_event_loop().run_until_complete(MainDB().connection())
