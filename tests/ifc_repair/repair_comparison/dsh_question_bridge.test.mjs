import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'node:http'
import { apply } from '../../../scripts/ifc_repair/repair_comparison/dsh/question-bridge.mjs'

async function fixture(t, respond) {
  const server = createServer(async (req, res) => {
    let raw = ''
    for await (const part of req) raw += part
    respond(JSON.parse(raw), res)
  })
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  t.after(() => { server.closeAllConnections(); server.close() })
  let listener
  apply({ on(event, callback) { assert.equal(event, 'user-questions/request'); listener = callback } },
    { endpoint: `http://127.0.0.1:${server.address().port}/questions` })
  return listener
}

const questions = [{ id: 'location', question: 'Which opening?' }]
const answer = { answers: [{ id: 'location', selected: [], custom: 'The western opening.' }] }

test('forwards only original questions and identity, waits for an external answer', async t => {
  let received, release
  const arrival = new Promise(resolve => { received = resolve })
  const ask = await fixture(t, (body, res) => {
    assert.equal(body.sessionId, 'session-one')
    assert.match(body.requestId, /^[a-f0-9-]{36}$/)
    assert.deepEqual(body.questions, questions)
    assert.deepEqual(Object.keys(body).sort(), ['questions', 'requestId', 'sessionId'])
    release = () => res.end(JSON.stringify({ requestId: body.requestId, ...answer }))
    received()
  })
  let settled = false
  const pending = ask({ agent: { id: 'session-one', privateField: 'do not forward' }, questions })
    .then(value => { settled = true; return value })
  await arrival
  assert.equal(settled, false)
  release()
  assert.deepEqual(await pending, answer)
})

for (const [label, mutate] of [
  ['wrong request', value => { value.requestId = 'stale' }],
  ['wrong question', value => { value.answers[0].id = 'other' }],
  ['missing answer', value => { value.answers = [] }],
  ['duplicate answer', value => { value.answers.push(value.answers[0]) }],
  ['unoffered option', value => { value.answers[0].selected = ['invented'] }],
]) {
  test(`rejects ${label} rather than resuming with invented facts`, async t => {
    const ask = await fixture(t, (body, res) => {
      const value = { requestId: body.requestId, ...structuredClone(answer) }
      mutate(value)
      res.end(JSON.stringify(value))
    })
    await assert.rejects(ask({ agent: { id: 'session-one' }, questions }), /INVALID_QUESTION_RESPONSE/)
  })
}

test('cancellation aborts a pending external question', async t => {
  let received
  const arrival = new Promise(resolve => { received = resolve })
  const ask = await fixture(t, () => received())
  const controller = new AbortController()
  const pending = ask({ agent: { id: 'session-one' }, questions, signal: controller.signal })
  const rejected = assert.rejects(pending, { name: 'AbortError' })
  await arrival
  controller.abort()
  await rejected
})
