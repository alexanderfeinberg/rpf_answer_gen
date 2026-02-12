import aiofiles

def is_pdf(file : bytes) -> bool:
    return file.startswith(b'%PDF')

async def read_file_async(filepath):
    async with aiofiles.open(filepath, 'r', encoding="utf-8") as f:
        return await f.read()
