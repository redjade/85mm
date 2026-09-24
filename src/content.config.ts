import { defineCollection, reference } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// 사진을 볼 때 내가 살피려는 여섯 가지. 글·연습·사진이 같은 말을 쓴다.
export const ELEMENTS = ['색', '빛', '대비', '공기', '이야기', '생략'] as const;
// 85mm에서는 인물/풍경보다 "얼마나 떨어져 있나"가 더 본질적인 구분이다.
export const DISTANCES = ['near', 'mid', 'far'] as const;

const element = z.enum(ELEMENTS);
const distance = z.enum(DISTANCES);

const learn = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/learn' }),
  schema: z.object({
    title: z.string(),
    order: z.number(),
    summary: z.string(),
    elements: z.array(element).default([]),
    widget: z.enum(['dof', 'frames']).optional(),
    sources: z
      .array(z.object({ label: z.string(), url: z.string().url() }))
      .default([]),
  }),
});

const drills = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/drills' }),
  schema: z.object({
    no: z.number(),
    title: z.string(),
    task: z.string(),
    constraint: z.string(),
    questions: z.array(z.string()).min(1),
    distance: z.array(distance).min(1),
    elements: z.array(element).default([]),
    time: z.string(),
  }),
});

const photos = defineCollection({
  // src/content/photos/<id>/index.md + photo.jpg  — tools/add_photo.py가 만든다
  loader: glob({
    pattern: '*/index.md',
    base: './src/content/photos',
    generateId: ({ entry }) => entry.replace(/\/index\.md$/, ''),
  }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      date: z.coerce.date(),
      image: image(),
      alt: z.string(),
      draft: z.boolean().default(false),
      // 촬영 정보 (EXIF에서 자동 추출, GPS는 저장하지 않는다)
      exif: z
        .object({
          fnumber: z.number().optional(),
          shutter: z.string().optional(),
          iso: z.number().optional(),
          focal: z.number().optional(),
          camera: z.string().optional(),
          lens: z.string().optional(),
        })
        .default({}),
      // 내가 적는 것
      distance: distance,
      mood: z.number().int().min(1).max(5), // 1 고요 … 5 흥분
      elements: z.array(element).default([]),
      drill: reference('drills').optional(),
      seen: z.string().default(''), // 무엇을 보았나
      omitted: z.string().default(''), // 무엇을 생략했나
      pair35: z.string().optional(), // 같은 장소 35mm 사진 id (있다면)
      source_hash: z.string().optional(),
    }),
});

export const collections = { learn, drills, photos };
