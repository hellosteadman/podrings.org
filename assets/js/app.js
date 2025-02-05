import '../scss/app.scss'
import AOS from 'aos'
import { Toast } from './toast'
import {} from 'bootstrap'
import {} from './itunes-search'
import {} from './modal'
import {} from './audio-player'
import {} from './upload'
import {} from './datefield'
import {} from './multiformat-select'
import {} from './download-btn'
import {} from './clipboard'
import {} from './share'

AOS.init(
    {
        offset: 80,
        duration: 1000,
        once: true,
        easing: 'ease'
    }
)

window.Podrings = {
    toast: (kind, message) => new Toast(
        {
            kind,
            message
        }
    ).show()
}
