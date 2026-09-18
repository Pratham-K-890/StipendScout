import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckIcon, PlusIcon, SaveIcon, XIcon } from 'lucide-react'
import { useState, type ComponentProps } from 'react'

import { getProfile, saveProfile } from '@/api/client'
import type {
  BaseProfile,
  EducationEntry,
  ExperienceEntry,
  HackathonEntry,
  ResponsibilityEntry,
} from '@/api/types'
import { AppHeader } from '@/components/AppHeader'
import { BulletsEditor } from '@/components/BulletsEditor'
import { ChipInput } from '@/components/ChipInput'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'

const EMPTY_PROFILE: BaseProfile = {
  name: '',
  email: '',
  phone: null,
  location: null,
  links: { linkedin: null, github: null, leetcode: null, portfolio: null },
  education: [],
  experience: [],
  hackathons: [],
  responsibilities: [],
  skills: {},
}

const EMPTY_EDUCATION: EducationEntry = {
  institution: '',
  degree: '',
  branch: null,
  start_year: null,
  end_year: null,
  cgpa: null,
}
const EMPTY_EXPERIENCE: ExperienceEntry = { title: '', company: '', start_date: '', end_date: null, bullets: [] }
const EMPTY_HACKATHON: HackathonEntry = { title: '', event: '', team_project: false, bullets: [] }
const EMPTY_RESPONSIBILITY: ResponsibilityEntry = { title: '', organization: '', bullets: [] }

function Field({ label, ...props }: { label: string } & ComponentProps<typeof Input>) {
  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Input {...props} />
    </div>
  )
}

function SkillsEditor({
  skills,
  onChange,
}: {
  skills: Record<string, string[]>
  onChange: (next: Record<string, string[]>) => void
}) {
  const entries = Object.entries(skills)

  function update(index: number, category: string, values: string[]) {
    const next = entries.map(([c, v], i): [string, string[]] => (i === index ? [category, values] : [c, v]))
    onChange(Object.fromEntries(next))
  }
  function remove(index: number) {
    onChange(Object.fromEntries(entries.filter((_, i) => i !== index)))
  }
  function add() {
    onChange(Object.fromEntries([...entries, [`Category ${entries.length + 1}`, []]]))
  }

  return (
    <div className="space-y-3">
      {entries.map(([category, values], i) => (
        <div key={i} className="space-y-2 rounded-lg border border-border p-3">
          <div className="flex items-center gap-2">
            <Input
              value={category}
              onChange={(e) => update(i, e.target.value, values)}
              className="h-7 max-w-56 text-xs font-medium"
              placeholder="Category name (e.g. Languages)"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="ml-auto"
              onClick={() => remove(i)}
              aria-label={`Remove ${category || 'category'}`}
            >
              <XIcon className="size-3.5" />
            </Button>
          </div>
          <ChipInput values={values} onChange={(v) => update(i, category, v)} placeholder="Add a skill…" />
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={add}>
        <PlusIcon /> Add category
      </Button>
    </div>
  )
}

export function ProfilePage() {
  const { data, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-secondary/40">
        <div className="mx-auto max-w-3xl space-y-4 px-6 py-10">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    )
  }

  // Keyed on whether a real profile existed, so switching from "no profile"
  // to "profile now saved" (or vice versa) remounts with fresh state
  // instead of an effect reconciling two sources of truth.
  return <ProfileForm key={data ? 'existing' : 'new'} initialProfile={data ?? EMPTY_PROFILE} />
}

function ProfileForm({ initialProfile }: { initialProfile: BaseProfile }) {
  const queryClient = useQueryClient()
  const [profile, setProfile] = useState(initialProfile)

  const mutation = useMutation({
    mutationFn: (p: BaseProfile) => saveProfile(p),
    onSuccess: (saved) => {
      queryClient.setQueryData(['profile'], saved)
    },
  })

  function set<K extends keyof BaseProfile>(key: K, value: BaseProfile[K]) {
    setProfile((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="min-h-screen bg-secondary/40">
      <AppHeader
        back
        eyebrow="Setup"
        title="Your Profile"
        subtitle="The static facts every tailored resume draws from. Projects aren't listed here — they're pulled live from GitHub per application."
        actions={
          <Button size="lg" onClick={() => mutation.mutate(profile)} disabled={mutation.isPending}>
            <SaveIcon /> {mutation.isPending ? 'Saving…' : 'Save Profile'}
          </Button>
        }
      />

      <div className="mx-auto max-w-3xl space-y-6 px-6 py-6">
        {mutation.isSuccess && (
          <div className="flex items-center gap-2 rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
            <CheckIcon className="size-4" /> Profile saved.
          </div>
        )}
        {mutation.isError && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            Save failed: {mutation.error.message}
          </div>
        )}

        <Card>
          <CardContent className="space-y-4">
            <h2 className="text-sm font-semibold text-foreground">Basics</h2>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Full name" value={profile.name} onChange={(e) => set('name', e.target.value)} />
              <Field label="Email" type="email" value={profile.email} onChange={(e) => set('email', e.target.value)} />
              <Field
                label="Phone"
                value={profile.phone ?? ''}
                onChange={(e) => set('phone', e.target.value || null)}
              />
              <Field
                label="Location"
                value={profile.location ?? ''}
                onChange={(e) => set('location', e.target.value || null)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              {(['linkedin', 'github', 'leetcode', 'portfolio'] as const).map((key) => (
                <Field
                  key={key}
                  label={key[0].toUpperCase() + key.slice(1)}
                  value={profile.links[key] ?? ''}
                  onChange={(e) => set('links', { ...profile.links, [key]: e.target.value || null })}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-2">
            <h2 className="text-sm font-semibold text-foreground">Skills</h2>
            <p className="text-xs text-muted-foreground">
              Grouped into categories — this is what a tailored resume renders as one line per category (e.g.
              &quot;Languages: Python, Java&quot;), and only the most JD-relevant skills within each are picked per
              application.
            </p>
            <SkillsEditor skills={profile.skills} onChange={(skills) => set('skills', skills)} />
          </CardContent>
        </Card>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Education</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => set('education', [...profile.education, { ...EMPTY_EDUCATION }])}
            >
              <PlusIcon /> Add education
            </Button>
          </div>
          {profile.education.map((entry, i) => (
            <Card key={i}>
              <CardContent className="space-y-3">
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => set('education', profile.education.filter((_, j) => j !== i))}
                    aria-label="Remove education entry"
                  >
                    <XIcon className="size-3.5" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field
                    label="Institution"
                    value={entry.institution}
                    onChange={(e) =>
                      set(
                        'education',
                        profile.education.map((x, j) => (j === i ? { ...x, institution: e.target.value } : x)),
                      )
                    }
                  />
                  <Field
                    label="Degree"
                    value={entry.degree}
                    onChange={(e) =>
                      set('education', profile.education.map((x, j) => (j === i ? { ...x, degree: e.target.value } : x)))
                    }
                  />
                  <Field
                    label="Branch"
                    value={entry.branch ?? ''}
                    onChange={(e) =>
                      set(
                        'education',
                        profile.education.map((x, j) => (j === i ? { ...x, branch: e.target.value || null } : x)),
                      )
                    }
                  />
                  <Field
                    label="CGPA"
                    value={entry.cgpa ?? ''}
                    onChange={(e) =>
                      set('education', profile.education.map((x, j) => (j === i ? { ...x, cgpa: e.target.value || null } : x)))
                    }
                  />
                  <Field
                    label="Start year"
                    type="number"
                    value={entry.start_year ?? ''}
                    onChange={(e) =>
                      set(
                        'education',
                        profile.education.map((x, j) =>
                          j === i ? { ...x, start_year: e.target.value ? Number(e.target.value) : null } : x,
                        ),
                      )
                    }
                  />
                  <Field
                    label="End year"
                    type="number"
                    value={entry.end_year ?? ''}
                    onChange={(e) =>
                      set(
                        'education',
                        profile.education.map((x, j) =>
                          j === i ? { ...x, end_year: e.target.value ? Number(e.target.value) : null } : x,
                        ),
                      )
                    }
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Experience</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => set('experience', [...profile.experience, { ...EMPTY_EXPERIENCE }])}
            >
              <PlusIcon /> Add experience
            </Button>
          </div>
          {profile.experience.map((entry, i) => (
            <Card key={i}>
              <CardContent className="space-y-3">
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => set('experience', profile.experience.filter((_, j) => j !== i))}
                    aria-label="Remove experience entry"
                  >
                    <XIcon className="size-3.5" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field
                    label="Title"
                    value={entry.title}
                    onChange={(e) =>
                      set('experience', profile.experience.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))
                    }
                  />
                  <Field
                    label="Company"
                    value={entry.company}
                    onChange={(e) =>
                      set('experience', profile.experience.map((x, j) => (j === i ? { ...x, company: e.target.value } : x)))
                    }
                  />
                  <Field
                    label="Start date (YYYY-MM)"
                    value={entry.start_date}
                    onChange={(e) =>
                      set(
                        'experience',
                        profile.experience.map((x, j) => (j === i ? { ...x, start_date: e.target.value } : x)),
                      )
                    }
                  />
                  <Field
                    label="End date (YYYY-MM, blank = ongoing)"
                    value={entry.end_date ?? ''}
                    onChange={(e) =>
                      set(
                        'experience',
                        profile.experience.map((x, j) => (j === i ? { ...x, end_date: e.target.value || null } : x)),
                      )
                    }
                  />
                </div>
                <BulletsEditor
                  bullets={entry.bullets}
                  onChange={(bullets) =>
                    set('experience', profile.experience.map((x, j) => (j === i ? { ...x, bullets } : x)))
                  }
                />
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Hackathons</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => set('hackathons', [...profile.hackathons, { ...EMPTY_HACKATHON }])}
            >
              <PlusIcon /> Add hackathon
            </Button>
          </div>
          {profile.hackathons.map((entry, i) => (
            <Card key={i}>
              <CardContent className="space-y-3">
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => set('hackathons', profile.hackathons.filter((_, j) => j !== i))}
                    aria-label="Remove hackathon entry"
                  >
                    <XIcon className="size-3.5" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field
                    label="Title"
                    value={entry.title}
                    onChange={(e) =>
                      set('hackathons', profile.hackathons.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))
                    }
                  />
                  <Field
                    label="Event"
                    value={entry.event}
                    onChange={(e) =>
                      set('hackathons', profile.hackathons.map((x, j) => (j === i ? { ...x, event: e.target.value } : x)))
                    }
                  />
                </div>
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <Checkbox
                    checked={entry.team_project}
                    onCheckedChange={(checked) =>
                      set(
                        'hackathons',
                        profile.hackathons.map((x, j) => (j === i ? { ...x, team_project: checked === true } : x)),
                      )
                    }
                  />
                  Team project
                </label>
                <BulletsEditor
                  bullets={entry.bullets}
                  onChange={(bullets) =>
                    set('hackathons', profile.hackathons.map((x, j) => (j === i ? { ...x, bullets } : x)))
                  }
                />
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Responsibilities</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => set('responsibilities', [...profile.responsibilities, { ...EMPTY_RESPONSIBILITY }])}
            >
              <PlusIcon /> Add responsibility
            </Button>
          </div>
          {profile.responsibilities.map((entry, i) => (
            <Card key={i}>
              <CardContent className="space-y-3">
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => set('responsibilities', profile.responsibilities.filter((_, j) => j !== i))}
                    aria-label="Remove responsibility entry"
                  >
                    <XIcon className="size-3.5" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field
                    label="Title"
                    value={entry.title}
                    onChange={(e) =>
                      set(
                        'responsibilities',
                        profile.responsibilities.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)),
                      )
                    }
                  />
                  <Field
                    label="Organization"
                    value={entry.organization}
                    onChange={(e) =>
                      set(
                        'responsibilities',
                        profile.responsibilities.map((x, j) => (j === i ? { ...x, organization: e.target.value } : x)),
                      )
                    }
                  />
                </div>
                <BulletsEditor
                  bullets={entry.bullets}
                  onChange={(bullets) =>
                    set('responsibilities', profile.responsibilities.map((x, j) => (j === i ? { ...x, bullets } : x)))
                  }
                />
              </CardContent>
            </Card>
          ))}
        </section>

        <div className="flex justify-end pb-10">
          <Button size="lg" onClick={() => mutation.mutate(profile)} disabled={mutation.isPending}>
            <SaveIcon /> {mutation.isPending ? 'Saving…' : 'Save Profile'}
          </Button>
        </div>
      </div>
    </div>
  )
}
