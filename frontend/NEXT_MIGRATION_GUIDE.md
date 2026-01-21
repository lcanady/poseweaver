# React 19 / Next.js 15 Migration Guide

## Overview

This project uses **Next.js 15.2** and **React 19**. This represents a
significant shift from React 18 patterns, particularly with the introduction of
new hooks for handling form state and optimistic updates.

## Critical React 19 Patterns

### 1. Form Actions & `useActionState`

Instead of manually handling `onSubmit` and loading states, use Server Actions
with `useActionState` (formerly `useFormState`).

**Old (React 18):**

```tsx
const [loading, setLoading] = useState(false);
const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await saveData(data);
    setLoading(false);
};
```

**New (React 19):**

```tsx
// actions.ts
"use server";
export async function saveData(prevState: any, formData: FormData) {
    return { message: "Saved!" };
}

// Component.tsx
import { useActionState } from "react";
import { saveData } from "./actions";

export default function MyForm() {
    const [state, formAction, isPending] = useActionState(
        saveData,
        initialState,
    );

    return (
        <form action={formAction}>
            <input name="field" />
            <button disabled={isPending}>Save</button>
        </form>
    );
}
```

### 2. `useFormStatus`

For child components of a form that need to know the loading state (e.g., a
submit button), use `useFormStatus`.

```tsx
import { useFormStatus } from "react-dom";

function SubmitButton() {
    const { pending } = useFormStatus();
    return <button disabled={pending}>{pending ? "Saving..." : "Save"}</button>;
}
```

_Note: `useFormStatus` only works if the component is rendered **inside** the
`<form>` element._

### 3. `useOptimistic`

For immediate UI feedback before the server responds.

```tsx
import { useOptimistic } from "react";

function MessageList({ messages }) {
    const [optimisticMessages, addOptimisticMessage] = useOptimistic(
        messages,
        (state, newMessage) => [...state, newMessage],
    );

    // Call addOptimisticMessage(msg) before server action
}
```

### 4. `ref` as a Prop

Forwarding refs is now simpler. `React.forwardRef` is largely unnecessary for
simple function components.

```tsx
// New
function MyInput({ placeholder, ref }) {
    return <input placeholder={placeholder} ref={ref} />;
}
```

### 5. Hydration & Third-Party Libraries

React 19 is stricter about hydration. If you see hydration errors:

- Ensure you aren't using browser-only APIs (like `window`) during standard
  render.
- Use `useEffect` or dynamic imports with `ssr: false` for client-only
  components that depend on browser APIs.
- Check if libraries are React 19 compatible. Many old libraries using
  `defaultProps` on function components will warn or fail.

## Styling (Tailwind + Radix)

We use `tailwindcss-animate` and Radix UI. Ensure strictly accessible HTML.

- **Do not use `div` for buttons.**
- Always include `aria-label` or visible labels.

## Next.js 15 Specifics

- **Caching**: Fetch requests are no longer cached by default in some contexts.
  Use `force-cache` if needed, or rely on the new default stale-while-revalidate
  behavior.
- **Async Request APIs**: `params` and `searchParams` in pages are now Promises.
  You must `await` them.

```tsx
// app/page.tsx
export default async function Page(
    { params }: { params: Promise<{ slug: string }> },
) {
    const { slug } = await params;
    return <div>{slug}</div>;
}
```
