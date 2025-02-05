(
    () => {
        const selector = 'a.btn[download]'
        const provision = (a) => {
            a.addEventListener('click',
                (e) => {
                    const btn = e.target.matches(selector) ? e.target : e.target.closest(selector)
                    const download = btn.download

                    if (!btn) {
                        return
                    }

                    const url = btn.href

                    try {
                        const tempLink = document.createElement('a')
                        tempLink.href = url
                        tempLink.setAttribute('download', download)
                        document.body.appendChild(tempLink)
                        tempLink.click()
                        
                        window.requestAnimationFrame(
                            () => document.body.removeChild(tempLink)
                        )

                        btn.classList.remove('btn-secondary')
                        btn.classList.add('btn-success')
                    } catch (error) {
                        window.location = url
                    }
                }
            )
        }

        document.querySelectorAll(selector).forEach(provision)
        document.addEventListener(
            'pr.modal.mount',
            (e) => e.target.querySelectorAll(selector).forEach(provision),
            true
        )
    }
)()
