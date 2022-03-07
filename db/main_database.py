import aiosqlite
import asyncio
from datetime import datetime
from config import MY_PEERS


class MainDB:

    async def connection(self):
        self.db: aiosqlite.Connection = await aiosqlite.connect("database.db")
        self.sql: aiosqlite.Cursor = await self.db.cursor()
        await self.sql.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER, hello_msg TEXT,"
                               " bye_msg TEXT, UNIQUE ('chat_id') ON CONFLICT IGNORE)")
        await self.sql.execute("CREATE TABLE IF NOT EXISTS stats (date DATE UNIQUE, income_messages INTEGER,"
                               " outcome_messages INTEGER, edited_messages INTEGER, outcome_event_answers INTEGER)")
        await self.sql.execute("CREATE TABLE IF NOT EXISTS rp_commands (command TEXT, emoji TEXT, action TEXT, "
                               "wom_action TEXT, specify TEXT, name_case INT, UNIQUE ('command') ON CONFLICT IGNORE)")
        await self.db.commit()
        return self

    async def get_registered_chats(self):
        await self.sql.execute("SELECT chat_id FROM chats")
        return await self.sql.fetchall()

    async def add_outcome(self, val_type: str, peer_id: int):
        if peer_id in MY_PEERS:
            return
        today = datetime.now().date()
        await self.sql.execute("INSERT OR IGNORE INTO stats VALUES (?, ?, ?, ?, ?)",
                               (today, 0, 0, 0, 0))
        if val_type == "outcome_message":
            await self.sql.execute("UPDATE stats SET outcome_messages = outcome_messages + 1 WHERE date = ?", (today,))
        elif val_type == "edit_message":
            await self.sql.execute("UPDATE stats SET edited_messages = edited_messages + 1 WHERE date = ?", (today,))
        elif val_type == "event_answer":
            await self.sql.execute("UPDATE stats SET outcome_event_answers = outcome_event_answers + 1 WHERE date = ?",
                                   (today,))
        await self.db.commit()

    async def add_income(self, peer_id: int):
        if peer_id in MY_PEERS:
            return
        today = datetime.now().date()
        await self.sql.execute("INSERT OR IGNORE INTO stats VALUES (?, ?, ?, ?, ?)",
                               (today, 1, 0, 0, 1))
        await self.sql.execute("UPDATE stats SET income_messages = income_messages + 1 WHERE date = ?", (today,))
        await self.db.commit()


main_db: MainDB = asyncio.get_event_loop().run_until_complete(MainDB().connection())
chat_ids = asyncio.get_event_loop().run_until_complete(main_db.get_registered_chats())
