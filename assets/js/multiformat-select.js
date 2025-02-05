import { info as toast } from './toast'

(
    () => {
        const provision = (div) => {
            const clipboardContent = {}

            const setClipboardContent = (item) => {
                switch (item.tagName) {
                    case 'TEXTAREA':
                        clipboardContent.type = 'text'
                        clipboardContent.value = item.value
                        break

                    case 'DIV':
                        clipboardContent.type = 'rich'
                        clipboardContent.value = item.innerHTML
                        break
                }
            }

            const firstItem = div.querySelector('[data-pr-format]:not(.d-none)')

            if (firstItem) {
                setClipboardContent(firstItem)
            }

            div.addEventListener('click',
                (e) => {
                    const option = e.target.matches('[data-pr-select]') ? e.target : e.target.closest('[data-pr-select]')
                    const select = option ? option.getAttribute('data-pr-select') : null
                    const dropdown = option ? option.closest('.dropdown') : null

                    if (!option) {
                        return
                    }

                    e.preventDefault()
                    
                    div.querySelectorAll('[data-pr-format]').forEach(
                        (el) => {
                            el.classList.add('d-none')
                        }
                    )

                    div.querySelectorAll(`[data-pr-format="${select}"]`).forEach(
                        (el) => {
                            el.classList.remove('d-none')
                            setClipboardContent(el)
                        }
                    )

                    if (dropdown) {
                        dropdown.querySelectorAll('.dropdown-item').forEach(
                            (el) => {
                                el.classList.remove('active')
                            }
                        )

                        dropdown.querySelectorAll(`[data-pr-select="${select}"]`).forEach(
                            (el) => {
                                el.classList.add('active')
                            }
                        )

                        dropdown.querySelectorAll('.multiformat-active-option').forEach(
                            (el) => {
                                el.innerText = option.innerText
                            }
                        )
                    }
                }
            )

            div.addEventListener('click',
                async (e) => {
                    const btn = e.target.matches('[data-pr-action="copy"]') ? e.target : e.target.closest('[data-pr-action="copy"]')

                    if (!btn) {
                        return
                    }

                    e.preventDefault()

                    if (clipboardContent.type === 'text') {
                        try {
                            await navigator.clipboard.writeText(clipboardContent.value)
                        } catch (err) {
                            console.error('Error copying text', err)
                            return
                        }

                        toast('Copied to clipboard.', 'clipboard-check-fill')
                        return
                    }

                    if (clipboardContent.type === 'rich') {
                        const data = [
                            new ClipboardItem(
                                {
                                    'text/html': new Blob(
                                        [clipboardContent.value],
                                        {
                                            type: 'text/html'
                                        }
                                    )
                                }
                            )
                        ]

                        try {
                            await navigator.clipboard.write(data)
                        } catch (err) {
                            console.error('Error copying rich text', err)
                            return
                        }

                        toast('Copied to clipboard.', 'clipboard-check-fill')
                    }
                }
            )

            div.addEventListener('click',
                (e) => {
                    const div = e.target.matches('[data-pr-format]') ? e.target : e.target.closest('[data-pr-format]')

                    if (!div) {
                        return
                    }

                    e.preventDefault()
                }
            )
        }

        document.querySelectorAll('.multiformat-select').forEach(provision)
        document.addEventListener(
            'pr.modal.mount',
            (e) => e.target.querySelectorAll('.multiformat-select').forEach(provision),
            true
        )
    }
)()