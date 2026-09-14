import { redirect } from 'next/navigation';

export default function Home() {
  // Redirect to Projects page (now the default homepage)
  redirect('/projects');
}
