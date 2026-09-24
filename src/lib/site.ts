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
