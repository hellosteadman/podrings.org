import { Toast as BsToast } from 'bootstrap'
import template from '../templates/toast.hbs'


class Toast {
    constructor ({kind, icon, date, message}) {
        this.kind = kind
        this.icon = icon
        this.date = date
        this.message = message
    }

    show () {
        const div = document.createElement('div')
        let container = document.body.querySelector('.toast-container')

        if (!container) {
            container = document.createElement('div')
            container.classList.add('toast-container')
            container.classList.add('position-fixed')
            container.classList.add('top-0')
            container.classList.add('end-0')
            container.classList.add('p-3')
            document.body.appendChild(container)
        }

        const ctx = {}

        if (this.kind) {
            ctx.kind = this.kind
        } else {
            ctx.kind = 'info'
        }

        if (this.icon) {
            ctx.icon = this.icon
        }

        if (this.message) {
            ctx.message = this.message
        }

        div.innerHTML = template(ctx)

        div.addEventListener('hidden.bs.toast',
            () => {
                container.removeChild(div)
            }
        )

        const child = div.querySelector('.toast')

        container.prepend(child)

        const toast = BsToast.getOrCreateInstance(child)
        
        setTimeout(() => toast.hide, 3000)
        toast.show()
    }
}

const info = (message, icon) => {
    const toast = new Toast(
        {
            kind: 'info',
            message: message,
            icon: icon
        }
    )

    toast.show()
}

const success = (message, icon) => {
    const toast = new Toast(
        {
            kind: 'success',
            message: message,
            icon: icon
        }
    )

    toast.show()
}

const warning = (message, icon) => {
    const toast = new Toast(
        {
            kind: 'warning',
            message: message,
            icon: icon
        }
    )

    toast.show()
}

const error = (message, icon) => {
    const toast = new Toast(
        {
            kind: 'danger',
            message: message,
            icon: icon
        }
    )

    toast.show()
}

export {
    Toast,
    info,
    success,
    warning,
    error
}
