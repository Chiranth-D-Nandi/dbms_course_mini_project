import { TicketPage } from '@/components/BookingFlow';
export default function Page({params}: {params: {pnr: string}}) { return <TicketPage pnr={Number(params.pnr)}/>; }
