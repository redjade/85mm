import { getCollection, type CollectionEntry } from 'astro:content';

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');

/** base('/85mm')를 붙인 내부 링크. 항상 끝에 / 를 붙인다. */
export function u(path = '/'): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  const withSlash = p.endsWith('/') || p.includes('#') ? p : `${p}/`;
  return `${BASE}${withSlash}`;
}

export const DISTANCE_LABEL = {
  near: '가까이',
  mid: '대화 거리',
  far: '멀리',
} as const;

export const DISTANCE_HINT = {
  near: '0.8–2m · 얼굴, 손, 사물',
  mid: '3–8m · 환경 속의 사람',
  far: '20m–∞ · 겹, 공기, 먼 빛',
} as const;

// 연습의 흐름. 1~6은 차례로, 7은 늘 되풀이한다.
export const STAGES: Record<number, { title: string; desc: string }> = {
  1: { title: '눈 바꾸기', desc: '35mm의 눈에서 85mm의 눈으로. 거리와 화각을 몸으로 익힌다.' },
  2: { title: '초점과 조리개', desc: '얕은 심도를 다룬다. 무엇을 선명하게, 무엇을 흐리게 둘지.' },
  3: { title: '프레임', desc: '넣고 빼기. 가운데와 비켜서기, 여백, 겹.' },
  4: { title: '빛과 색', desc: '피사체보다 빛과 색을 먼저 본다. 찍을 때와 보정할 때 모두.' },
  5: { title: '멀리, 그리고 사람 사이', desc: '풍경의 겹과 공기, 군중 속 한 사람.' },
  6: { title: '머물기', desc: '시간을 들여 한 곳을 오래 본다.' },
  7: { title: '늘 하는 연습', desc: '순서와 상관없이 되풀이한다. 나갔다 올 때마다, 한 주마다, 한 달마다.' },
};
export const ALWAYS_STAGE = 7;

export function stageLabel(n: number): string {
  return n === ALWAYS_STAGE ? STAGES[n].title : `${n}단계 · ${STAGES[n].title}`;
}

export const MOOD_LABEL = ['', '고요', '잔잔', '중간', '들뜸', '흥분'] as const;

export async function getPhotos(): Promise<CollectionEntry<'photos'>[]> {
  const all = await getCollection('photos', (p) => !p.data.draft);
  return all.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
}

export async function getDrills() {
  const all = await getCollection('drills');
  return all.sort((a, b) => a.data.no - b.data.no);
}

export async function getLearn() {
  const all = await getCollection('learn');
  return all.sort((a, b) => a.data.order - b.data.order);
}

export function fmtDate(d: Date): string {
  // frontmatter의 시각(시간대 없음)은 UTC로 읽히므로 UTC로 꺼내야 찍은 날짜 그대로 나온다
  return `${d.getUTCFullYear()}.${String(d.getUTCMonth() + 1).padStart(2, '0')}.${String(d.getUTCDate()).padStart(2, '0')}`;
}

export function exifLine(e: CollectionEntry<'photos'>['data']['exif']): string {
  return [
    e.focal ? `${e.focal}mm` : null,
    e.fnumber ? `f/${e.fnumber}` : null,
    e.shutter ? `${e.shutter}s` : null,
    e.iso ? `ISO ${e.iso}` : null,
  ]
    .filter(Boolean)
    .join(' · ');
}

export function drillNo(n: number): string {
  return String(n).padStart(2, '0');
}
