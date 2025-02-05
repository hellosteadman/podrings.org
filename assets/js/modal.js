import { getCookie } from './helpers'
import { Modal } from 'bootstrap'

(
    () => {
        document.addEventListener('click',
            (e) => {
                const selector = '[href][data-bs-toggle="modal"][data-bs-target]'
                const btn = e.target.matches(selector) ? e.target : e.target.closest(selector)
                const target = btn ? btn.getAttribute('data-bs-target') : ''
                const modal = target ? document.querySelector(target) : null

                if (!btn) {
                    return
                }

                if (btn.href.startsWith('javascript:;') || btn.href.startsWith('#')) {
                    return
                }

                e.preventDefault()
                
                if (modal) {
                    modal.querySelectorAll('.modal-content').forEach(
                        async (container) => {
                            const response = await fetch(
                                btn.href,
                                {
                                    headers: {
                                        'X-Requested-With': 'XMLHttpRequest',
                                        'X-Display-As': 'modal'
                                    }
                                }
                            )

                            container.innerHTML = await response.text()

                            window.requestAnimationFrame(
                                () => {
                                    const input = container.querySelector('input:not([readonly]):not([disabled])')

                                    if (input) {
                                        input.focus()
                                    }
                                }
                            )

                            modal.dispatchEvent(
                                new CustomEvent('pr.modal.mount')
                            )
                        }
                    )
                }
            },
            false
        )

        document.addEventListener('shown.bs.modal',
            (e) => {
                const input = e.target.querySelector('input:not([readonly]):not([disabled])')

                if (input) {
                    input.focus()
                }
            },
            false
        )

        document.addEventListener('submit',
            (e) => {
                const form = e.target.matches('form') ? e.target : e.target.closest('form')
                const modal = form ? form.closest('.modal') : null

                if (!modal) {
                    return
                }

                e.preventDefault()

                modal.querySelectorAll('.modal-content').forEach(
                    (container) => {
                        const promise = fetch(
                            form.action,
                            {
                                body: new FormData(form),
                                method: form.method ? form.method.toUpperCase() : 'GET',
                                headers: {
                                    'X-Requested-With': 'XMLHttpRequest',
                                    'X-Display-As': 'modal',
                                    'X-CSRFToken': getCookie('csrftoken')
                                }
                            }
                        )

                        form.querySelectorAll('input, button').forEach(
                            (el) => {
                                el.disabled = true
                            } 
                        )

                        promise.then(
                            async (response) => {
                                container.innerHTML = await response.text()
                                modal.dispatchEvent(
                                    new CustomEvent('pr.modal.mount')
                                )
                            }
                        ).catch(console.error)
                    }
                )
            },
            false
        )

        document.querySelectorAll('.modal.show-on-load').forEach(
            async (modal) => {
                const preload = modal.getAttribute('data-pr-preload')
                const container = modal.querySelector('.modal-content')

                if (preload) {
                    const response = await fetch(
                        preload,
                        {
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest',
                                'X-Display-As': 'modal'
                            }
                        }
                    )

                    container.innerHTML = await response.text()

                    window.requestAnimationFrame(
                        () => {
                            const input = container.querySelector('input:not([readonly]):not([disabled])')

                            if (input) {
                                input.focus()
                            }
                        }
                    )

                    modal.dispatchEvent(
                        new CustomEvent('pr.modal.mount')
                    )
                }

                new Modal(modal).toggle()
            }
        )
    }
)()
