import asyncio

import asyncpg


DATABASE_URL = "postgresql://postgres:Postgresql4Life!@localhost:5432/echocare_db"


async def main() -> None:
    print(f"Trying to connect with: {DATABASE_URL}")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected successfully!")
        await conn.close()
    except Exception as e:  # noqa: BLE001
        print("❌ Connection failed:")
        print(repr(e))


if __name__ == "__main__":
    asyncio.run(main())


