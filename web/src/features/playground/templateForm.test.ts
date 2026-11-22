import { describe, expect, it } from 'vitest'
import { fieldErrorsFrom, fieldsComplete, findTemplate } from './templateForm'

const help = { name: 'help', fields: [] }
const unknown = { name: 'unknown_command', fields: ['command'] }

describe('template form helpers', () => {
  it('finds the selected template', () => {
    expect(findTemplate([help, unknown], 'unknown_command')).toBe(unknown)
    expect(findTemplate([help], null)).toBeNull()
  })

  it('is complete when every field has a non-blank value', () => {
    expect(fieldsComplete(help, {})).toBe(true)
    expect(fieldsComplete(unknown, { command: ' ' })).toBe(false)
    expect(fieldsComplete(unknown, { command: 'x' })).toBe(true)
    expect(fieldsComplete(null, {})).toBe(false)
  })

  it('maps a 422 naming a field to that field', () => {
    expect(fieldErrorsFrom({ status: 422, message: 'Missing field: command' }, ['command'])).toEqual({ command: 'Missing field: command' })
    expect(fieldErrorsFrom({ status: 422, message: 'Invalid', fieldErrors: { command: 'Field required' } }, ['command'])).toEqual({
      command: 'Field required',
    })
    expect(fieldErrorsFrom({ status: 422, message: 'Message too long' }, ['command'])).toEqual({})
    expect(fieldErrorsFrom({ status: 404, message: 'Unknown template command' }, ['command'])).toEqual({})
  })
})
