def my_bookings(request):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.user.role != 'PATIENT':
        return redirect('home')

    now = timezone.now()
    today = now.date()

    #  AUTO-EXPIRE PENDING BOOKINGS (TIME-BASED)
    expired_bookings = Booking.objects.filter(
        patient=request.user,
        status='PENDING',
        expires_at__isnull=False,
        expires_at__lt=now
    )

    for booking in expired_bookings:
        with transaction.atomic():
            booking.status = 'EXPIRED'
            booking.save(update_fields=['status'])

            if booking.slot:
                slot = BookingSlot.objects.select_for_update().get(
                    pk=booking.slot.pk
                )
                slot.booked_count = F('booked_count') - 1
                slot.save(update_fields=['booked_count'])

    bookings = Booking.objects.filter(
        patient=request.user
    ).order_by('-created_at')

    paginator = Paginator(bookings, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'patient/booking_list.html', {
        'bookings': page_obj,
        'today': today,   # 👈 REQUIRED for template
        'now': now,
    })

#daily revnue chart for payment for labadmin
dates = []
    revenues = []
    #last 7 days including today
    for i in range(6,-1,-1):
        day = today -timedelta(days=i)

        total = (
            Payment.objects.filter(
                lab=lab, 
                status='SUCCESS',
                created_at__date=day).aggregate(total=Sum('amount'))['total'] or 0
    )
        
        dates.append(day.strftime("%d %b"))
        revenues.append(float(total))


        <div style="width:100%; height:300px;">
                        <canvas id="monthlyRevenueChart"></canvas>
                    </div>
                    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                    <script>
                        const ctx = document.getElementById('monthlyRevenueChart');

                        new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: {{ dates|safe }},
                                // labels: {{ months|safe }},
                                datasets: [{
                                    label: 'Daily Revenue (₹)',
                                    data: {{ revenues|safe }},
                                    fill: false,
                                    tension: 0.3
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false
                            }
                        });
                    </script>
        
        ##monthly revenue(success only booking) starts here
    monthly_data = (
        Payment.objects.filter(lab=lab, status='SUCCESS')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    months = []
    revenues = []

    for entry in monthly_data:
        month_name = calendar.month_abbr[entry['month'].month]
        months.append(month_name)
        revenues.append(float(entry['total']))
    # monthly revenue(success only booking) ends here


    def payment_success(request,booking_id):
    if not request.user.is_authenticated or request.user.role != 'PATIENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403) 

       
    
    #to prevent from paying the expired bookings
    if booking.status == 'EXPIRED':
        return JsonResponse({'error': 'Booking expired'}, status=400)
    
    data = json.loads(request.body)

    booking = Booking.objects.get(
        pk=booking_id,
        patient=request.user
    )
    payment = booking.payment # OneToOne relation
    payment.status = 'SUCCESS'
    payment.paid_at = timezone.now()
    payment.razorpay_payment_id = data.get('razorpay_payment_id')
    payment.razorpay_order_id = data.get('razorpay_order_id')
    payment.razorpay_signature = data.get('razorpay_signature')
    payment.save(update_fields=['status','razorpay_payment_id','razorpay_order_id','razorpay_signature','paid_at'])

    booking.status = 'CONFIRMED'
    booking.payment_status = 'SUCCESS'
    booking.save(update_fields=['status','payment_status'])
    print(booking.payment_status)
    print(booking.status)
    
    return JsonResponse({"status": "ok"})

@login_required
def lab_payment_list(request):
    chart_type = request.GET.get('chart', 'daily')  
    lab = get_lab_from_request(request)

    expire_pending_bookings(lab=lab)
    payments = Payment.objects.filter(lab=lab)

    #status filter
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)

    #date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        payments = payments.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        payments = payments.filter(created_at__date__lte=parse_date(end_date))

    #search query
    search_query = request.GET.get('search')
    if search_query:
        payments= payments.filter(
            Q(patient__email__icontains=search_query) |
            Q(booking__id__icontains=search_query) 
            
        )

    payments = payments.select_related('booking','patient').order_by('-created_at')
    

    stats = payments.values('status').annotate(total=Count('id')).order_by('status')

    #total revenuew
    total_revenue = payments.filter(status='SUCCESS').aggregate(total=Sum('amount'))['total'] or 0

    #Today collection
    today = timezone.now().date()
    today_collection = payments.filter(
        status='SUCCESS',
        created_at__date = today
    ).aggregate(total=Sum('amount'))['total']or 0


    #Pending Count
    pending_count = payments.filter(status='PENDING').count()

    failed_count = payments.filter(status='FAILED').count()
    #daily revneue
    labels = []
    revenues = []
    
    if chart_type == 'monthly':
        # Last 6 months
        for i in range(5, -1, -1):
            month_date = (today.replace(day=1) - timedelta(days=30*i))
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            total = (
                Payment.objects.filter(
                    lab=lab,
                    status='SUCCESS',
                    created_at__gte=month_start,
                    created_at__lt=month_end
                ).aggregate(total=Sum('amount'))['total'] or 0
            )

            labels.append(calendar.month_abbr[month_start.month])
            revenues.append(float(total))

    else:
        # Default: Daily (Last 7 Days)
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)

            total = (
                Payment.objects.filter(
                    lab=lab,
                    status='SUCCESS',
                    created_at__date=day
                ).aggregate(total=Sum('amount'))['total'] or 0
            )

            labels.append(day.strftime("%d %b"))
            revenues.append(float(total))

    
    
    page = Paginator(payments,5)
    
    page_number = request.GET.get('page',1) #Get the page number from the URL (?page=2)


    #Get the correct page from the paginator

    page_obj = page.get_page(page_number)

    return render(request,'lab/payment_list.html',{
        'payments':page_obj,
        'stats':stats,
        'status_selected':status,
        'start_date':start_date or '',
        'end_date':end_date or '',
        'total_revenue': total_revenue,
        'today_collection': today_collection,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'labels': labels,
        'revenues': revenues,
        'chart_type':chart_type
        # 'months': months, #for monthly revenue
        # 'revenues': revenues, #for monthly revenue

    })


#-----------------------------------------#
#EXPORT CSV FOR LABADMIN
#-----------------------------------------#
@login_required
def export_payments_csv(request):
    if request.user.role != 'LAB_ADMIN':
        messages.error(request,'Please login as LABADMIN.')
        return redirect('login')
    
    lab = get_lab_from_request(request)

    #filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')

    payments = Payment.objects.filter(lab=lab).order_by('-created_at')
    
    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)
    
    if end_date:
        payments = payments.filter(created_at__date__lte=end_date)
    
    if status:
        payments = payments.filter(status__iexact=status) # case-insensitive match
        # 2. Add Debugging (Check your console)
    print(f"DEBUG: Status Filter is '{status}'")
    print(f"DEBUG: Found {payments.count()} records")

        #csv respose
    filename = f'payments_{datetime.now().strftime("%Y%m%d")}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"' #download as csv insted of displying as text
    
    writer = csv.writer(response)

    #header row
    writer.writerow([
        "Booking ID",
        "Patient Email",
        "Amount",
        "Status",
        "Razorpay Order ID",
        "Razorpay Payment ID",
        "Paid At",
        "Created At",
    ])

    total_amount = Decimal('0.00')
    # Optional: Print the count to your console to debug while testing
    print(f"Found {payments.count()} payments for status {status}")

    for payment in payments:
        try:
            
            current_amount = payment.amount
            total_amount += current_amount 

            # 2. Use .get() or getattr to prevent crashes if relationships are missing then N/A
            booking_id = payment.booking.id if payment.booking else "N/A"
            patient_email = payment.patient.email if payment.patient else "No Email"

            writer.writerow([
                booking_id,
                patient_email,
                current_amount,
                payment.status,
                payment.razorpay_order_id or '',
                payment.razorpay_payment_id or '',
                payment.paid_at.strftime('%Y-%m-%d %H:%M') if payment.paid_at else '',
                payment.created_at.strftime('%Y-%m-%d %H:%M') if payment.created_at else '',

            ])
            #add total row

        except Exception as e:
            print(f"Error on Row {payment.id}: {str(e)}")
    writer.writerow([])
    writer.writerow(['','TOTAL',total_amount])


    return response
