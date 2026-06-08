import type { OutlookDraftProfile } from '#src-core/types/outlook-draft-profile.types'
import { buildOutlookEmail } from '#src-core/utils/build-outlook-email'
import { generateOutlookPassword } from '#src-core/utils/generate-outlook-password'
import {
  outlookNamePairKey,
  registerUsedOutlookNamePair,
  type OutlookNamePair,
} from '#src-core/utils/outlook-account-names'
import { randomUsFullName } from '#src-core/utils/us-outlook-names'

/**
 * Génère des profils Outlook pour inscription manuelle sur signup.live.com.
 */
export function generateOutlookDraftProfiles(
  count: number,
  birthday: string,
  usedNamePairs: OutlookNamePair[],
): OutlookDraftProfile[] {
  if (count < 1) {
    throw new Error('Le nombre de profils doit être au moins 1.')
  }

  const birthDate: string = birthday.trim()

  if (!birthDate) {
    throw new Error('Indiquez une date de naissance avant de générer les profils.')
  }

  const pairs: OutlookNamePair[] = [...usedNamePairs]
  const seenKeys: Set<string> = new Set(
    pairs.map((pair: OutlookNamePair) => outlookNamePairKey(pair.firstName, pair.lastName)),
  )
  const recentPasswords: string[] = []
  const drafts: OutlookDraftProfile[] = []

  for (let index: number = 0; index < count; index += 1) {
    const { firstName, lastName } = randomUsFullName(pairs)
    registerUsedOutlookNamePair(pairs, seenKeys, firstName, lastName)

    const password: string = generateOutlookPassword(recentPasswords)
    recentPasswords.push(password)

    drafts.push({
      id: crypto.randomUUID(),
      selected: true,
      firstName,
      lastName,
      birthday: birthDate,
      email: buildOutlookEmail(firstName, lastName),
      password,
      saved: false,
    })
  }

  return drafts
}
