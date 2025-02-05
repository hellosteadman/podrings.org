import { TempusDominus } from '@eonasdan/tempus-dominus';
import moment from 'moment'

(
    () => {
        const provision = (input) => {
            const optionsAttr = input.getAttribute('data-td-options')
            const widgetOpts = optionsAttr ? JSON.parse(optionsAttr) : {}
            const options = {}
            const localization = {
                format: 'yyyy-MM-dd',
                startOfTheWeek: 1
            }

            const display = {
                icons: {
                    'previous': 'bi bi-chevron-left',
                    'next': 'bi bi-chevron-right',
                    'today': 'bi bi-calendar-check',
                    'clear': 'bi bi-trash',
                    'close': 'bi bi-xmark'
                },
                buttons: {
                    'today': false,
                    'clear': false,
                    'close': false
                },
                components: {
                    calendar: true,
                    date: true,
                    month: true,
                    year: true,
                    decades: true,
                    clock: false,
                    hours: false,
                    minutes: false,
                    seconds: false
                }
            }

            const restrictions = {}

            if (widgetOpts.date) {
                options.defaultDate = moment(widgetOpts.date, 'YYYY-MM-DD').toDate()
            }

            if (widgetOpts.minDate) {
                restrictions.minDate = moment(widgetOpts.minDate, 'YYYY-MM-DD').toDate()
            }

            options.localization = localization
            options.display = display

            if (Object.keys(restrictions).length) {
                options.restrictions = restrictions
            }

            new TempusDominus(input, options)
        }

        document.querySelectorAll('input.datetimepicker-input').forEach(provision)
        document.addEventListener(
            'pr.modal.mount',
            (e) => e.target.querySelectorAll('input.datetimepicker-input').forEach(provision),
            true
        )
    }
)()