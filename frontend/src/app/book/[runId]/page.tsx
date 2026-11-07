import { BookingForm } from '@/components/BookingFlow';
export default function Page({params}: {params: {runId: string}}) { return <BookingForm runId={Number(params.runId)}/>; }
