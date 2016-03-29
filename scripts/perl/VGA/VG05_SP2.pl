#! /usr/bin/perl -w
# VG05_SP2.pl -- MySQL:Textwert:ivv7srv16.uni-muenster.de
# Variantenspektren in ECM_Acts_Sp fŸr Hss. einzelner Kapitel auf der Basis von ECM_Acts_Base anlegen

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_Sp_01:localhost";	# data source name

my $user_name = getUsername();						# user name
my $password = getPassword();						# password



my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

###AKTUELL ZU BEARBEITENDES KAPITEL###
my $chn = 6;
my $chnstr;
my $chnstr2;
if ($chn < 10)
{
	$chnstr = 'Apg0'.$chn;
	$chnstr2 = '0'.$chn;
} else {
	$chnstr = 'Apg'.$chn;
	$chnstr2 = $chn;
}

my $source1 = '`ECM_Acts_Mss`.`ActsMsList`';
my $source2 = '`ECM_Acts_Base`.`05'.$chnstr2.'Witn`';
my $source3 = '`ECM_Acts_Base`.`05'.$chnstr2.'Rdg`';

my ($sth, @ary, $ary, $gtxt, $ueges, $lac, $hsnr, @msl, $ms, @cpmsl, $cpms);

$sth = $dbh->prepare ("SELECT MS FROM $source1 WHERE `$chnstr` = 1");
$sth->execute();
	
while (@ary = $sth->fetchrow_array())
{
	@msl = (@msl, @ary);
}

foreach $ms(@msl)
{
	my $target = '`ECM_Acts_Sp_'.$chnstr2.'`.`Acts'.$chnstr2.'_'.$ms.'`';

	$dbh->do ("DROP TABLE IF EXISTS $target;");

 	$dbh->do ("CREATE  TABLE  $target (  
	 `ANFADR` int( 11  )  default NULL ,
	 `ENDADR` int( 11  )  default NULL ,
	 `LABEZ` varchar( 32  )  collate utf8_unicode_ci  default NULL ,
	 `LABEZSUF` varchar( 32  )  collate utf8_unicode_ci  default NULL ,
	 `HSNR` int( 11  )  default NULL 
	  ) ENGINE  = InnoDB  DEFAULT CHARSET  = utf8 COLLATE  = utf8_unicode_ci;");

	$dbh->do ("INSERT INTO $target SELECT ANFADR, ENDADR, LABEZ, LABEZSUF, HSNR FROM $source2 WHERE HSNR = $ms;");
	
	$dbh->do ("ALTER TABLE $target ADD `BYZ` varchar(1);");
	
	$sth = $dbh->prepare ("SELECT ANFADR, ENDADR, LABEZ FROM $source3 WHERE `BYZ` LIKE 'B'");
	$sth->execute();
	
	while (@ary = $sth->fetchrow_array())
	{
		$dbh->do ("UPDATE $target SET `BYZ` = 'B' WHERE `ANFADR` = $ary[0] AND `ENDADR` = $ary[1] AND `LABEZ` LIKE '$ary[2]'");
	}
	
}



$sth->finish ();

$dbh->disconnect ();

exit (0);
