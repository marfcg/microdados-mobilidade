require(ggplot2)
df2 <- read.csv('../data/src_RJ-tgt_RJ-grav_model_rss_aic_beta_1.20-2.50_gamma_2.00-3.50.csv')

p = ggplot(df2, aes(x=beta, y=gamma, z=Log_10.ER.))
c.plot <- p + stat_contour(breaks=seq(1,10), aes(colour = ..level..)) +
  ggtitle(bquote(F[jk]%prop%T[j]~m[k]^beta/~r[jk]^gamma)) + 
  xlab(expression(beta)) + 
  ylab(expression(gamma)) +
  labs(colour=expression(Log[10](ER)))
ggsave('src_RJ-tgt_RJ-grav_model_rss_aic_beta_1.20-2.50_gamma_2.00-3.50.pdf')

c.plot2 <- p + 
  geom_raster(aes(fill=Log_10.ER.)) + 
  labs(fill=expression(Log[10](ER))) + 
  stat_contour(breaks=1, color='black') +
  scale_fill_gradientn(colours=RColorBrewer::brewer.pal(9, 'Blues'), 
                       na.value='transparent', breaks=seq(0,10,2), 
                       labels=seq(0,10,2), limits=c(0,10)) + 
  xlim(1.5, 1.8) + 
  ylim(2.4, 3.25) +
  ggtitle(bquote(F[jk]%prop%T[j]~m[k]^beta/~r[jk]^gamma)) + 
  xlab(expression(beta)) + 
  ylab(expression(gamma))
  
ggsave('src_RJ-tgt_RJ-grav_model_rss_aic_beta_1.20-2.50_gamma_2.00-3.50_filled.pdf')