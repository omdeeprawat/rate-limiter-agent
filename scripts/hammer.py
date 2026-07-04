import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def hammer(client_id: str, total_requests: int, capacity: int):
  async with httpx.AsyncClient(base_url=BASE_URL) as client:
    tasks = [
      client.get("/check_limit", params={"client_id": client_id})
      for _ in range(total_requests)
    ]
    responses = await asyncio.gather(*tasks)

  allows = sum(1 for r in responses if r.json()["status"] == "ALLOW")
  denies = sum(1 for r in responses if r.json()["status"] == "DENY")

  print(f"\nclient_id : {client_id}")
  print(f"total     : {total_requests}")
  print(f"ALLOW     : {allows}  (expected: {capacity})")
  print(f"DENY      : {denies}  (expected: {total_requests - capacity})")
  print(f"verdict   : {'✓ PASS' if allows == capacity else '✗ FAIL — atomicity broken'}")


async def main():
  # single client, 50 concurrent requests, bucket capacity 10
  await hammer("stress-single", total_requests=50, capacity=10)

  # reset between tests
  await asyncio.sleep(0.1)

  # multiple clients concurrently — each should get exactly 10 Allows
  await asyncio.gather(
    hammer("stress-client-a", total_requests=30, capacity=10),
    hammer("stress-client-b", total_requests=30, capacity=10),
    hammer("stress-client-c", total_requests=30, capacity=10),
  )


asyncio.run(main())