(
    () => {
        const provision = (el) => {
            const href = el.getAttribute('data-audiocontext')
            const progress = el.querySelector('.progress-bar')
            let player = null

            el.addEventListener('click',
                (e) => {
                    const selector = '[data-pr-action="playpause"]'
                    const btn = e.target.matches(selector) ? e.target : e.target.closest(selector)

                    if (!btn) {
                        return
                    }

                    e.preventDefault()

                    if (btn.disabled) {
                        return
                    }

                    if (player === null) {
                        btn.disabled = true
                        btn.classList.add('disabled')

                        player = new Audio()
                        player.addEventListener('play',
                            () => {
                                btn.innerHTML = '<i class="bi-pause-circle-fill"></i>'

                                document.querySelectorAll('[data-audiocontext]').forEach(
                                    (other) => {
                                        if (other === el) {
                                            return
                                        }

                                        other.dispatchEvent(
                                            new CustomEvent('pr.audio.stop')
                                        )
                                    }
                                )
                            }
                        )

                        player.addEventListener('pause',
                            () => {
                                btn.innerHTML = '<i class="bi-play-circle-fill"></i>'
                            }
                        )

                        player.addEventListener('canplay',
                            () => {
                                btn.disabled = false
                                btn.classList.remove('disabled')
                                player.play()
                            }
                        )

                        if (progress) {
                            player.addEventListener('timeupdate',
                                () => {
                                    player.setAttribute('aria-valuenow', player.currentTime)
                                    window.requestAnimationFrame(
                                        () => {
                                            const percent = player.currentTime / player.duration * 100
                                            progress.style.width = `${percent}%`
                                        }
                                    )
                                }
                            )
                        }

                        player.src = href
                    } else {
                        if (player.paused) {
                            player.play()
                        } else {
                            player.pause()
                        }
                    }
                }
            )

            el.addEventListener('pr.audio.stop',
                () => {
                    if (player) {
                        player.pause()
                    }
                },
                true
            )
        }

        document.querySelectorAll('[data-audiocontext]').forEach(provision)
        document.addEventListener(
            'pr.modal.mount',
            (e) => e.target.querySelectorAll('[data-audiocontext]').forEach(provision),
            true
        )
    }
)()
