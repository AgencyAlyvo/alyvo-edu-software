/**
 *
 */
export type SignInResponse = {
  type: 'bearer'
  value: string
  expiresAt: string | null
}

/**
 *
 */
export type SignUpResponse = {
  type: 'bearer'
  value: string
  expiresAt: string | null
}
