// Cordis answerer only: the official ask-user tool owns model-facing semantics.
import { randomUUID } from 'node:crypto'

export const name = 'repair-comparison-question-bridge'
export const inject = ['userQuestions']

export function apply(ctx, config) {
  const endpoint = new URL(config.endpoint)
  if (!['http:', 'https:'].includes(endpoint.protocol) || endpoint.username || endpoint.password) {
    throw new Error('INVALID_QUESTION_ENDPOINT')
  }
  ctx.on('user-questions/request', async request => {
    const sessionId = request.agent?.id
    if (typeof sessionId !== 'string' || !sessionId) throw new Error('QUESTION_SESSION_REQUIRED')
    const requestId = randomUUID()
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ requestId, sessionId, questions: request.questions }),
      signal: request.signal,
      redirect: 'error',
    })
    if (!response.ok) throw new Error(`QUESTION_TRANSPORT_FAILED:${response.status}`)
    const value = await response.json()
    const invalid = () => { throw new Error('INVALID_QUESTION_RESPONSE') }
    if (value?.requestId !== requestId || !Array.isArray(value.answers)
      || value.answers.length !== request.questions.length) invalid()
    const seen = new Set()
    for (const answer of value.answers) {
      const question = request.questions.find(item => item.id === answer?.id)
      if (!question || seen.has(answer.id) || !Array.isArray(answer.selected)
        || answer.selected.some(label => typeof label !== 'string'
          || !question.options?.some(option => option.label === label))
        || new Set(answer.selected).size !== answer.selected.length
        || (!question.multiSelect && answer.selected.length > 1)
        || (answer.custom !== undefined && typeof answer.custom !== 'string')
        || (!answer.selected.length && !answer.custom?.trim())) invalid()
      seen.add(answer.id)
    }
    // Strip controller metadata; only the confirmed answer reaches the tool.
    return { answers: value.answers.map(({ id, selected, custom }) => ({
      id, selected, ...(custom === undefined ? {} : { custom }),
    })) }
  })
}
