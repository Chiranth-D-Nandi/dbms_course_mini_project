import { TrainPage } from '@/components/BookingFlow';
export default function Page({params}: {params: {id: string}}) { return <TrainPage trainId={Number(params.id)}/>; }
