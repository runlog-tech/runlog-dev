import type { Register } from 'claude-code'

// Measurement only: appends one JSON row per turn to $CONTEXT_METER_LOG; with that unset it does nothing.
export const register: Register = on => {
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    try {
      const path = await $.env.get('CONTEXT_METER_LOG')
      if (path) {
        const usage = await $.session.usage()
        const row = JSON.stringify({
          at: await $.clock.now(),
          session: await $.session.id(),
          turns: await $.session.turns(),
          context: usage.context,
          rateLimits: usage.rateLimits,
          cost: usage.cost,
        })
        let previous = ''
        try {
          const text = await $.fs.read(path)
          if (typeof text === 'string') previous = text
        } catch {}
        await $.fs.write(path, previous + row + '\n')
      }
    } catch {}
    return result
  })
}
