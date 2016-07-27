df2 <- read.csv('../data/src_RJ-tgt_RJ-grav_model_rss_aic_beta_1.20-2.50_gamma_2.00-3.50.csv')
p = ggplot(df2, aes(x=beta, y=gamma, z=Log_10.ER., colour=`Log(ER)`))
c.plot <- p + stat_contour(breaks=seq(1,10), aes(colour = ..level..)) + ggtitle(bquote(F[jk]%prop%T[j]~m[k]^beta/~r[jk]^gamma)) + xlab(expression(beta)) + ylab(expression(gamma))
ggsave('src_RJ-tgt_RJ-grav_model_rss_aic_beta_1.20-2.50_gamma_2.00-3.50.pdf')
