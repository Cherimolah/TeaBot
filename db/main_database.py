import aiosqlite3
import asyncio
from datetime import datetime
from config import MY_PEERS


class MainDB:

    async def connection(self):
        self.db: aiosqlite3.Connection = await aiosqlite3.connect("database.db")
        self.sql: aiosqlite3.Cursor = await self.db.cursor()
        await self.sql.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER, hello_msg TEXT,"
                               " bye_msg TEXT, UNIQUE ('chat_id') ON CONFLICT IGNORE)")
        await self.sql.execute("CREATE TABLE IF NOT EXISTS stats (date DATE UNIQUE, income_messages INTEGER,"
                               " outcome_messages INTEGER, edited_messages INTEGER, outcome_event_answers INTEGER)")
        await self.db.commit()
        return self

    async def get_registered_chats(self):
        await self.sql.execute("SELECT chat_id FROM chats")
        return await self.sql.fetchall()

    async def add_outcome(self, value: str, peer_id: int):
        if peer_id in MY_PEERS:
            return
        assert value not in ["outcome_messages, edited_messages, outcome_event_answers"]
        today = datetime.now().date()
        await self.sql.execute(f"INSERT OR IGNORE INTO stats VALUES (?, ?, ?, ?, ?);",
                               (today, 0, 0, 0, 0))
        await self.sql.execute("UPDATE stats SET outcome_messages = outcome_messages + 1 WHERE date = ?", (today,))
        await self.db.commit()


main_db: MainDB = asyncio.get_event_loop().run_until_complete(MainDB().connection())
chat_ids = asyncio.get_event_loop().run_until_complete(main_db.get_registered_chats())
