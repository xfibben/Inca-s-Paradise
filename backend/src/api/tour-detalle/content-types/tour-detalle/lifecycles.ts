function computeEndDate(data: Record<string, any>) {
  const { startDate, durationDays } = data;
  if (startDate && durationDays && durationDays >= 1) {
    const start = new Date(startDate);
    start.setDate(start.getDate() + durationDays - 1);
    data.endDate = start.toISOString().split('T')[0];
  }
}

export default {
  beforeCreate(event: any) {
    computeEndDate(event.params.data);
  },
  beforeUpdate(event: any) {
    computeEndDate(event.params.data);
  },
};
