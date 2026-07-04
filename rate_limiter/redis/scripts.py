

RATE_LIMIT_SCRIPT = """
-- KEYS[1] = "rate_limit:{client_id}"
-- ARGV[1] = max_tokens        (your self.max_tokens)
-- ARGV[2] = refill_rate       (your self.refill_rate)
-- ARGV[3] = interval          (your self.interval)
-- ARGV[4] = now               (unix timestamp from Python)
-- ARGV[5] = tokens_requested  (default 1, supports your allow_request(tokens=N))
-- ARGV[6] = ttl               (key expiry seconds)

local key              = KEYS[1]
local max_tokens       = tonumber(ARGV[1])
local refill_rate      = tonumber(ARGV[2])
local interval         = tonumber(ARGV[3])
local now              = tonumber(ARGV[4])
local tokens_requested = tonumber(ARGV[5])
local ttl              = tonumber(ARGV[6])

-- Read current state
local data        = redis.call('HMGET', key, 'tokens', 'refilled_at')
local tokens      = tonumber(data[1])
local refilled_at = tonumber(data[2])

-- First request: initialize full bucket
if tokens == nil then
    tokens      = max_tokens
    refilled_at = now
end

-- Discrete refill - exact mirror of your Python _refill()
local elapsed     = math.max(0, now - refilled_at)
local num_refills = math.floor(elapsed / interval)
if num_refills > 0 then
    tokens      = math.min(max_tokens, tokens + num_refills * refill_rate)
    refilled_at = refilled_at + num_refills * interval  -- same pattern you used
end

-- Consume tokens
local allowed = 0
if tokens >= tokens_requested then
    tokens  = tokens - tokens_requested
    allowed = 1
end

-- Persist updated state + reset TTL
redis.call('HSET', key, 'tokens', tostring(math.floor(tokens)), 'refilled_at', string.format("%.6f",refilled_at))
redis.call('EXPIRE', key, ttl)

-- Return: [allowed, remaining (floored), next_refill_unix_timestamp]
-- next_refill mirrors your get_reset_time(): refilled_at + interval
local next_refill = math.floor(refilled_at + interval)
return {allowed, math.floor(tokens), next_refill}
"""

